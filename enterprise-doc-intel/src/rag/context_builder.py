"""Assembles retrieval results into a structured prompt context with source attribution."""

from __future__ import annotations

import logging

from src.config import settings
from src.rag.retriever import RetrievalResult

logger = logging.getLogger(__name__)


def build_context(retrieval: RetrievalResult) -> str:
    """Format retrieval results into a context string for the LLM.

    Includes source attribution so the generator can cite documents.
    Caps total context at settings.max_context_chars to avoid exceeding model limits.
    """
    parts: list[str] = []
    char_budget = settings.max_context_chars

    # Vector search results
    if retrieval.vector_results:
        parts.append("## Retrieved Documents\n")
        for i, result in enumerate(retrieval.vector_results, 1):
            source = result.metadata.get("source", "unknown")
            score = f"{result.score:.3f}"
            header = f"[Source {i}: {source} (relevance: {score})]"
            entry = f"{header}\n{result.text}\n"
            if len("\n".join(parts)) + len(entry) > char_budget:
                logger.info("Context budget reached after %d sources", i - 1)
                break
            parts.append(header)
            parts.append(result.text)
            parts.append("")

    # Knowledge graph context
    if retrieval.graph_context:
        graph_section = f"## Knowledge Graph Context\n\n{retrieval.graph_context}"
        if len("\n".join(parts)) + len(graph_section) <= char_budget:
            parts.append("## Knowledge Graph Context\n")
            parts.append(retrieval.graph_context)

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
