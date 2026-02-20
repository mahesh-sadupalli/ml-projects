"""Hybrid retriever: combines vector search (ChromaDB) with graph context (Neo4j)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.embeddings.provider import get_single_embedding
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.knowledge_graph.query import extract_entities_from_query, get_graph_context
from src.vectorstore.chroma import ChromaStore, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Combined retrieval result from vector store and knowledge graph."""

    vector_results: list[SearchResult] = field(default_factory=list)
    graph_context: str = ""


def retrieve(
    query: str,
    chroma: ChromaStore,
    neo4j: Neo4jClient | None = None,
    top_k: int = 5,
) -> RetrievalResult:
    """Retrieve relevant context using hybrid vector + graph search.

    1. Embed the query and search ChromaDB for similar chunks.
    2. If Neo4j is available, find mentioned entities and pull graph context.
    3. Return combined results.
    """
    # Vector search
    query_embedding = get_single_embedding(query)
    vector_results = chroma.search(query_embedding, top_k=top_k)
    logger.info("Vector search returned %d results", len(vector_results))

    # Graph search (optional, graceful degradation)
    graph_context = ""
    if neo4j:
        try:
            entities = extract_entities_from_query(query, neo4j)
            if entities:
                graph_context = get_graph_context(entities, neo4j)
                logger.info("Graph context from %d entities", len(entities))
        except Exception:
            logger.warning("Graph search failed, proceeding with vector results only")

    return RetrievalResult(vector_results=vector_results, graph_context=graph_context)
