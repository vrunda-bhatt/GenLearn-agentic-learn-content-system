from __future__ import annotations

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    run_id: str
    topic: str
    inject_fault: bool
    attempt_number: int
    max_retries: int
    prompt_version: str
    evaluator_version: str
    memory_snapshot: dict[str, Any]
    memory_hits: list[str]
    lesson: str
    claims: list[dict[str, str]]
    fact_check: dict[str, Any]
    hard_validation: dict[str, Any]
    rubric_evaluation: dict[str, Any]
    rejection_log: list[dict[str, Any]]
    final_status: str
    final_output: dict[str, Any]
    repair_notes: list[str]
