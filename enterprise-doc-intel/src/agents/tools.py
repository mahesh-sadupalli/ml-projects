"""Agent tools — callable functions the agent can invoke during multi-step reasoning."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

import ollama as ollama_client

from src.config import settings
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.rag.retriever import retrieve
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """A tool the agent can call."""

    name: str
    description: str
    fn: Callable[..., str]


def search_documents(query: str, *, chroma: ChromaStore, neo4j: Neo4jClient | None = None) -> str:
    """Search the document store and return relevant passages."""
    result = retrieve(query, chroma, neo4j, top_k=3)
    if not result.vector_results:
        return "No relevant documents found."

    parts = []
    for i, r in enumerate(result.vector_results, 1):
        source = r.metadata.get("source", "unknown")
        parts.append(f"[{i}] ({source}, score={r.score:.3f}): {r.text[:500]}")

    if result.graph_context:
        parts.append(f"\n{result.graph_context}")

    return "\n\n".join(parts)


def query_knowledge_graph(entity: str, *, neo4j: Neo4jClient) -> str:
    """Query the knowledge graph for information about an entity."""
    neighbors = neo4j.get_neighbors(entity, max_hops=2)
    if not neighbors:
        # Try searching
        matches = neo4j.search_entities(entity, limit=5)
        if not matches:
            return f"No information found about '{entity}' in the knowledge graph."
        return f"Related entities: {', '.join(m['name'] for m in matches)}"

    lines = [f"Neighbors of '{entity}':"]
    for n in neighbors[:15]:
        labels = ", ".join(n["labels"])
        lines.append(f"  - {n['name']} ({labels}), distance={n['distance']}")
    return "\n".join(lines)


def summarize(text: str) -> str:
    """Summarize a long piece of text using the LLM."""
    response = ollama_client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "user", "content": f"Summarize the following text concisely:\n\n{text[:4000]}"},
        ],
        options={"temperature": 0.1},
    )
    return response["message"]["content"]


def compare_documents(query: str, *, chroma: ChromaStore) -> str:
    """Search for documents related to a comparison query and present them side by side."""
    result = retrieve(query, chroma, top_k=6)
    if not result.vector_results:
        return "No documents found for comparison."

    # Group results by source
    by_source: dict[str, list[str]] = {}
    for r in result.vector_results:
        source = r.metadata.get("source", "unknown")
        by_source.setdefault(source, []).append(r.text[:300])

    parts = []
    for source, texts in by_source.items():
        parts.append(f"=== {source} ===")
        parts.append("\n".join(texts))
        parts.append("")

    return "\n".join(parts)


def build_tools(chroma: ChromaStore, neo4j: Neo4jClient | None = None) -> list[Tool]:
    """Build the list of tools available to the agent."""
    tools = [
        Tool(
            name="search_documents",
            description="Search the document store for passages relevant to a query. Input: a search query string.",
            fn=lambda q: search_documents(q, chroma=chroma, neo4j=neo4j),
        ),
        Tool(
            name="summarize",
            description="Summarize a long piece of text. Input: the text to summarize.",
            fn=summarize,
        ),
        Tool(
            name="compare_documents",
            description="Find and compare documents on a topic. Input: a comparison query.",
            fn=lambda q: compare_documents(q, chroma=chroma),
        ),
    ]

    if neo4j:
        tools.append(
            Tool(
                name="query_knowledge_graph",
                description="Look up an entity in the knowledge graph to find related concepts. Input: entity name.",
                fn=lambda e: query_knowledge_graph(e, neo4j=neo4j),
            )
        )

    return tools
