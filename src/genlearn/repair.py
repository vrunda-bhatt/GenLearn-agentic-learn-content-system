from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .facts import get_fact_pack


@dataclass
class LessonRepairer:
    def repair(
        self,
        *,
        topic: str,
        lesson: str,
        claims: list[dict[str, str]],
        failed_criteria: list[str],
    ) -> tuple[str, list[dict[str, str]]]:
        repaired_claims = [{"claim_id": fact.claim_id, "statement": fact.statement} for fact in get_fact_pack(topic)]
        fact_lines = "\n".join(f"- {claim['statement']}" for claim in repaired_claims)
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
            f"Repair focus: {', '.join(sorted(set(failed_criteria))) if failed_criteria else 'none'}."
        )
        return lesson, repaired_claims
