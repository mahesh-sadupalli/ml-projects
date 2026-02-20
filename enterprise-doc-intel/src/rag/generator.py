"""LLM generation with Ollama — produces answers with citations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import ollama as ollama_client

from src.config import settings
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.rag.context_builder import build_context, build_prompt
from src.rag.retriever import retrieve
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """The final answer with metadata."""

    answer: str
    sources: list[dict] = field(default_factory=list)
    graph_context: str = ""


def generate_answer(
    question: str,
    chroma: ChromaStore,
    neo4j: Neo4jClient | None = None,
    top_k: int = 5,
) -> GenerationResult:
    """Full RAG pipeline: retrieve → build context → generate answer."""
    # 1. Retrieve
    retrieval = retrieve(question, chroma, neo4j, top_k=top_k)

    # 2. Build context
    context = build_context(retrieval)

    # 3. Generate
    prompt = build_prompt(question, context)
    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1},
    )

    answer = response["message"]["content"]

    # Collect source metadata
    sources = [
        {"source": r.metadata.get("source", "unknown"), "score": r.score}
        for r in retrieval.vector_results
    ]

    return GenerationResult(
        answer=answer,
        sources=sources,
        graph_context=retrieval.graph_context,
    )
