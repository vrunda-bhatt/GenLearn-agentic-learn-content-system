from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .facts import FactClaim, get_fact_pack


@dataclass
class LessonGenerator:
    def generate(self, *, topic: str, attempt_number: int, inject_fault: bool, memory_snapshot: dict[str, Any], prior_feedback: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]], list[str]]:
        facts = get_fact_pack(topic)
        lesson, claims = self._template_generate(facts, memory_snapshot)
        if inject_fault and attempt_number == 1 and claims:
            claims[0] = {
                "claim_id": "fault_wrong_retrieval_order",
                "statement": "RAG generates an answer first and only retrieves supporting facts afterward.",
            }
        return lesson, claims, self._memory_hits(memory_snapshot)

    def _template_generate(self, facts: list[FactClaim], memory_snapshot: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
        claims = [{"claim_id": fact.claim_id, "statement": fact.statement} for fact in facts]
        fact_lines = "\n".join(f"- {claim['statement']}" for claim in claims)
        memory_hint = self._memory_hint(memory_snapshot)
        lesson = (
            f"# Introduction to RAG\n\n"
            f"## What is RAG\n"
            f"RAG means Retrieval-Augmented Generation. In plain language, it is a way to help an AI answer by finding useful information first and then using that information to write the response.\n\n"
            f"## Why it matters\n"
            f"RAG matters because a model can sound confident even when it does not know the right answer. By retrieving relevant notes or documents, it can give answers that are more specific and better grounded.\n\n"
            f"## How it works\n"
            f"Think of RAG as a two-step helper. First, it retrieves documents or passages that look relevant. Second, it passes that context to the model so the model can generate a better answer. The two key ideas are retrieval and generation.\n\n"
            f"## Beginner example\n"
            f"Imagine a study helper for a course. You ask, 'What is the deadline for the project?' The system searches the course guide, finds the right page, and then writes an answer using those notes. That is easier to trust than guessing from memory alone.\n\n"
            f"## Key ideas\n"
            f"Useful beginner terms are document, passage, retrieval, context, and generation. A document is the source text, a passage is a smaller piece of it, retrieval means finding the useful piece, context is the information passed into the model, and generation is the part where the model writes the answer.\n\n"
            f"## Fact list\n"
            f"{fact_lines}\n\n"
            f"{memory_hint}\n"
            f"Attempt note: 1."
        )
        return lesson, claims

    def _memory_hits(self, memory_snapshot: dict[str, Any]) -> list[str]:
        memory_hits: list[str] = []
        for item in memory_snapshot.get("common_failures", []):
            memory_hits.append(f"prior-failure:{item}")
        for item in memory_snapshot.get("successful_fixes", []):
            memory_hits.append(f"prior-fix:{item}")
        return memory_hits

    def _memory_hint(self, memory_snapshot: dict[str, Any]) -> str:
        common_failures = memory_snapshot.get("common_failures", [])
        if not common_failures:
            return ""
        return "\n".join(["## Memory hint", f"Earlier runs often struggled with: {', '.join(common_failures)}.", "This draft keeps those points explicit."])
