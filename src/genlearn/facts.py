from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactClaim:
    claim_id: str
    statement: str
    keywords: tuple[str, ...]


RAG_FACTS: dict[str, list[FactClaim]] = {
    "Introduction to RAG": [
        FactClaim(
            claim_id="rag_definition",
            statement="RAG means Retrieval-Augmented Generation: a system that retrieves relevant information and uses it to help generate an answer.",
            keywords=("retrieval-augmented generation", "retrieve", "generate"),
        ),
        FactClaim(
            claim_id="rag_why_matters",
            statement="RAG matters because it helps models answer with fresher, more specific, and more grounded information than memory alone.",
            keywords=("fresher", "specific", "grounded", "memory"),
        ),
        FactClaim(
            claim_id="rag_how_works",
            statement="RAG usually works by retrieving documents or passages first, then giving that context to the model before generation.",
            keywords=("retrieving", "documents", "context", "before generation"),
        ),
        FactClaim(
            claim_id="rag_two_parts",
            statement="The two key ideas are retrieval and generation.",
            keywords=("retrieval", "generation"),
        ),
        FactClaim(
            claim_id="rag_example",
            statement="A beginner example is a study helper that searches a course guide, then writes an answer using the retrieved notes.",
            keywords=("study helper", "course guide", "retrieved notes"),
        ),
        FactClaim(
            claim_id="rag_jargon_help",
            statement="Useful beginner terms include document, passage, retrieval, context, and generation.",
            keywords=("document", "passage", "retrieval", "context", "generation"),
        ),
    ]
}


def get_fact_pack(topic: str) -> list[FactClaim]:
    if topic not in RAG_FACTS:
        raise ValueError(f"Unsupported topic: {topic}")
    return RAG_FACTS[topic]
