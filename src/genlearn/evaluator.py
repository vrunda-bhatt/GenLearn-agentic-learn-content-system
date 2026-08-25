from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .facts import FactClaim, get_fact_pack


@dataclass
class DeterministicFactChecker:
    def fact_check(self, topic: str, claims: list[dict[str, str]]) -> dict[str, Any]:
        expected_claims = {fact.claim_id: fact for fact in get_fact_pack(topic)}
        issues: list[dict[str, str]] = []
        grounded_claims: list[dict[str, str]] = []

        for claim in claims:
            claim_id = claim.get("claim_id", "")
            statement = claim.get("statement", "")
            expected = expected_claims.get(claim_id)
            if expected is None:
                issues.append({"claim_id": claim_id, "reason": "unknown claim id"})
                continue
            if not self._statement_matches_fact(statement, expected):
                issues.append({"claim_id": claim_id, "reason": "statement does not match curated fact pack"})
                continue
            grounded_claims.append(claim)

        missing = [claim_id for claim_id in expected_claims if claim_id not in {c.get("claim_id") for c in grounded_claims}]
        for claim_id in missing:
            issues.append({"claim_id": claim_id, "reason": "required fact missing from claims list"})

        passed = not issues
        return {"passed": passed, "issues": issues, "grounded_claims": grounded_claims, "failed": [issue["claim_id"] for issue in issues]}

    def _statement_matches_fact(self, statement: str, fact: FactClaim) -> bool:
        text = statement.lower()
        return all(keyword in text for keyword in fact.keywords[:2]) or fact.statement.lower() == text


@dataclass
class HardValidator:
    def validate(self, lesson: str, claims: list[dict[str, str]], fact_check: dict[str, Any]) -> dict[str, Any]:
        required_sections = ["What is RAG", "Why it matters", "How it works", "Beginner example", "Key ideas"]
        missing_sections = [section for section in required_sections if section.lower() not in lesson.lower()]
        has_claims = bool(claims)
        has_grounded_claims = fact_check.get("passed", False)
        lesson_not_empty = len(lesson.split()) >= 120

        checks = {
            "has_required_sections": (not missing_sections, "missing sections: " + ", ".join(missing_sections) if missing_sections else "present"),
            "has_structured_claims": (has_claims, "claims list present" if has_claims else "claims list missing"),
            "claims_are_grounded": (has_grounded_claims, "claims matched fact pack" if has_grounded_claims else "some claims failed grounding"),
            "sufficient_length": (lesson_not_empty, "lesson is long enough" if lesson_not_empty else "lesson is too short"),
        }
        failed = [name for name, (passed, _) in checks.items() if not passed]
        return {"passed": not failed, "checks": {name: {"passed": passed, "reason": reason} for name, (passed, reason) in checks.items()}, "failed": failed}


@dataclass
class RubricEvaluator:
    def evaluate(self, *, topic: str, lesson: str, claims: list[dict[str, str]], fact_check: dict[str, Any], hard_validation: dict[str, Any], memory_snapshot: dict[str, Any]) -> dict[str, Any]:
        return self._deterministic_evaluate(lesson)

    def _deterministic_evaluate(self, lesson: str) -> dict[str, Any]:
        lower_lesson = lesson.lower()
        section_positions = [lower_lesson.find("## what is rag"), lower_lesson.find("## why it matters"), lower_lesson.find("## how it works"), lower_lesson.find("## beginner example"), lower_lesson.find("## key ideas")]

        jargon_terms = ["embedding", "vector", "retrieval", "context", "generation"]
        jargon_definitions = all(self._term_is_explained(lesson, term) for term in jargon_terms if term in lower_lesson)

        checks = {
            "covers_what_it_is": ("what is rag" in lower_lesson or "rag means" in lower_lesson, "definition present" if ("what is rag" in lower_lesson or "rag means" in lower_lesson) else "definition missing"),
            "covers_why_it_matters": ("why it matters" in lower_lesson or "helps" in lower_lesson, "benefit explained" if ("why it matters" in lower_lesson or "helps" in lower_lesson) else "benefit missing"),
            "covers_how_it_works": ("how it works" in lower_lesson or "retriev" in lower_lesson, "workflow explained" if ("how it works" in lower_lesson or "retriev" in lower_lesson) else "workflow missing"),
            "mentions_retrieval": ("retrieval" in lower_lesson or "retrieve" in lower_lesson, "retrieval mentioned" if ("retrieval" in lower_lesson or "retrieve" in lower_lesson) else "retrieval missing"),
            "mentions_generation": ("generation" in lower_lesson or "generate" in lower_lesson, "generation mentioned" if ("generation" in lower_lesson or "generate" in lower_lesson) else "generation missing"),
            "has_beginner_example": ("for example" in lower_lesson or "imagine" in lower_lesson or "beginner example" in lower_lesson, "example present" if ("for example" in lower_lesson or "imagine" in lower_lesson or "beginner example" in lower_lesson) else "example missing"),
            "defines_jargon": (jargon_definitions, "jargon is explained" if jargon_definitions else "one or more terms are unexplained"),
            "coherent_flow": (self._is_reasonable_section_order(section_positions), "flow is coherent" if self._is_reasonable_section_order(section_positions) else "sections are out of order or too sparse"),
        }
        failed = [name for name, (passed, _) in checks.items() if not passed]
        return {"passed": not failed, "checks": {name: {"passed": passed, "reason": reason} for name, (passed, reason) in checks.items()}, "failed": failed, "source": "deterministic"}

    def _term_is_explained(self, lesson: str, term: str) -> bool:
        text = lesson.lower()
        term_index = text.find(term)
        if term_index == -1:
            return True
        markers = ["means", "is", "refers to", "helps", "in plain language", "that is"]
        while term_index != -1:
            window = text[max(0, term_index - 80) : term_index + 120]
            if any(marker in window for marker in markers):
                return True
            term_index = text.find(term, term_index + len(term))
        return False

    def _is_reasonable_section_order(self, positions: list[int]) -> bool:
        positions = [position for position in positions if position >= 0]
        return positions == sorted(positions) and len(positions) >= 4
