"""Assembles retrieval results into a structured prompt context with source attribution."""

from __future__ import annotations

from src.rag.retriever import RetrievalResult


def build_context(retrieval: RetrievalResult) -> str:
    """Format retrieval results into a context string for the LLM.

    Includes source attribution so the generator can cite documents.
    """
    parts: list[str] = []

    # Vector search results
    if retrieval.vector_results:
        parts.append("## Retrieved Documents\n")
        for i, result in enumerate(retrieval.vector_results, 1):
            source = result.metadata.get("source", "unknown")
            score = f"{result.score:.3f}"
            parts.append(f"[Source {i}: {source} (relevance: {score})]")
            parts.append(result.text)
            parts.append("")

    # Knowledge graph context
    if retrieval.graph_context:
        parts.append(f"## {retrieval.graph_context}")

    return "\n".join(parts)


def build_prompt(question: str, context: str) -> str:
    """Build the final prompt for the LLM with context and question."""
    return f"""\
You are an intelligent document assistant. Answer the question based on the provided context.
Always cite your sources using [Source N] notation. If the context doesn't contain enough
information to answer, say so clearly.

{context}

---
Question: {question}

Answer:"""
