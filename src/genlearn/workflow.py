from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from .config import EVALUATOR_VERSION, MAX_RETRIES, PROMPT_VERSION
from .evaluator import DeterministicFactChecker, HardValidator, RubricEvaluator
from .generator import LessonGenerator
from .memory import MemoryStore, ensure_data_dirs
from .repair import LessonRepairer
from .state import WorkflowState


def build_graph() -> Any:
    ensure_data_dirs()
    memory = MemoryStore.load()
    generator = LessonGenerator()
    fact_checker = DeterministicFactChecker()
    hard_validator = HardValidator()
    rubric_evaluator = RubricEvaluator()
    repairer = LessonRepairer()

    graph = StateGraph(WorkflowState)
    graph.add_node(
        "load_memory",
        lambda state: {
            "memory_snapshot": memory.summary_for_topic(state["topic"]),
            "prompt_version": PROMPT_VERSION,
            "evaluator_version": EVALUATOR_VERSION,
            "max_retries": MAX_RETRIES,
            "rejection_log": state.get("rejection_log", []),
            "attempt_number": state.get("attempt_number", 1),
        },
    )
    graph.add_node("generate", lambda state: _generate_node(generator, state))
    graph.add_node("fact_check", lambda state: {"fact_check": fact_checker.fact_check(state["topic"], state.get("claims", []))})
    graph.add_node("hard_validate", lambda state: {"hard_validation": hard_validator.validate(state.get("lesson", ""), state.get("claims", []), state.get("fact_check", {}))})
    graph.add_node(
        "rubric_evaluate",
        lambda state: {
            "rubric_evaluation": rubric_evaluator.evaluate(
                topic=state["topic"],
                lesson=state.get("lesson", ""),
                claims=state.get("claims", []),
                fact_check=state.get("fact_check", {}),
                hard_validation=state.get("hard_validation", {}),
                memory_snapshot=state.get("memory_snapshot", {}),
            )
        },
    )
    graph.add_node("repair", lambda state: _repair_node(repairer, state))
    graph.add_node("finalize", lambda state: _finalize_node(state))

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "generate")
    graph.add_edge("generate", "fact_check")
    graph.add_edge("fact_check", "hard_validate")
    graph.add_edge("hard_validate", "rubric_evaluate")

    def needs_repair(state: WorkflowState) -> str:
        passed = state.get("fact_check", {}).get("passed", False) and state.get("hard_validation", {}).get("passed", False) and state.get("rubric_evaluation", {}).get("passed", False)
        if passed:
            return "finalize"
        if state.get("attempt_number", 1) >= state.get("max_retries", MAX_RETRIES):
            return "finalize"
        return "repair"

    graph.add_conditional_edges("rubric_evaluate", needs_repair, {"repair": "repair", "finalize": "finalize"})
    graph.add_edge("repair", "fact_check")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_workflow(topic: str, inject_fault: bool = False) -> dict[str, Any]:
    memory = MemoryStore.load()
    run_id = str(uuid.uuid4())
    graph = build_graph()
    initial_state: WorkflowState = {
        "run_id": run_id,
        "topic": topic,
        "inject_fault": inject_fault,
        "attempt_number": 1,
        "max_retries": MAX_RETRIES,
        "prompt_version": PROMPT_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "memory_snapshot": {},
        "memory_hits": [],
        "rejection_log": [],
        "repair_notes": [],
    }
    result = graph.invoke(initial_state)

    final_payload = result.get("final_output", {})
    if final_payload:
        final_payload["rejection_log"] = result.get("rejection_log", [])
        final_payload["attempt_number"] = result.get("attempt_number", 1)
    memory.record_run(
        {
            "run_id": run_id,
            "topic": topic,
            "attempts": result.get("rejection_log", []),
            "status": result.get("final_status", "failed"),
            "inject_fault": inject_fault,
        }
    )
    return final_payload or result


def _generate_node(generator: LessonGenerator, state: WorkflowState) -> dict[str, Any]:
    lesson, claims, memory_hits = generator.generate(
        topic=state["topic"],
        attempt_number=state.get("attempt_number", 1),
        inject_fault=state.get("inject_fault", False),
        memory_snapshot=state.get("memory_snapshot", {}),
        prior_feedback=list(state.get("rejection_log", [])),
    )
    return {"lesson": lesson, "claims": claims, "memory_hits": memory_hits}


def _repair_node(repairer: LessonRepairer, state: WorkflowState) -> dict[str, Any]:
    failed_criteria = _collect_failed_criteria(state)
    fix_applied = _repair_strategy(failed_criteria)
    repaired_lesson, repaired_claims = repairer.repair(
        topic=state["topic"],
        lesson=state.get("lesson", ""),
        claims=state.get("claims", []),
        failed_criteria=failed_criteria,
    )
    rejection_log = list(state.get("rejection_log", []))
    rejection_log.append(
        {
            "attempt_number": state.get("attempt_number", 1),
            "failed_criteria": failed_criteria,
            "root_cause": ", ".join(failed_criteria) if failed_criteria else "passed",
            "fix_applied": fix_applied,
            "repair_feedback": failed_criteria,
            "changed": {
                "lesson": "repaired",
                "claims": "fault removed" if any(claim.get("claim_id") == "fault_wrong_retrieval_order" for claim in state.get("claims", [])) else "unchanged",
            },
        }
    )
    return {
        "lesson": repaired_lesson,
        "claims": repaired_claims,
        "repair_notes": [fix_applied],
        "attempt_number": state.get("attempt_number", 1) + 1,
        "rejection_log": rejection_log,
    }


def _finalize_node(state: WorkflowState) -> dict[str, Any]:
    passed = state.get("rubric_evaluation", {}).get("passed", False) and state.get("hard_validation", {}).get("passed", False) and state.get("fact_check", {}).get("passed", False)
    result = {
        "run_id": state["run_id"],
        "topic": state["topic"],
        "status": "passed" if passed else "failed",
        "prompt_version": state.get("prompt_version", PROMPT_VERSION),
        "evaluator_version": state.get("evaluator_version", EVALUATOR_VERSION),
        "inject_fault": state.get("inject_fault", False),
        "memory_hits": state.get("memory_hits", []),
        "rejection_log": state.get("rejection_log", []),
        "attempt_number": state.get("attempt_number", 1),
        "lesson": state.get("lesson", ""),
        "claims": state.get("claims", []),
        "evaluation": {
            "fact_check": state.get("fact_check", {}),
            "hard_validation": state.get("hard_validation", {}),
            "rubric": state.get("rubric_evaluation", {}),
        },
    }
    return {"final_status": result["status"], "final_output": result}


def _collect_failed_criteria(state: WorkflowState) -> list[str]:
    failed: list[str] = []
    for key in ("fact_check", "hard_validation", "rubric_evaluation"):
        failed.extend(state.get(key, {}).get("failed", []))
    return failed


def _repair_strategy(failed_criteria: list[str]) -> str:
    if not failed_criteria:
        return "No repair was needed"
    return "Preserved the passing lesson structure and explicitly fixed: " + ", ".join(sorted(set(failed_criteria)))
