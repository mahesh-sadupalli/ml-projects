"""Unit tests for the hybrid retriever (mocked embeddings + stores)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.rag.retriever import RetrievalResult, retrieve
from src.vectorstore.chroma import SearchResult


def _make_search_result(text: str = "chunk", source: str = "doc.md", score: float = 0.9) -> SearchResult:
    return SearchResult(id="c1", text=text, metadata={"source": source}, score=score)


@patch("src.rag.retriever.get_single_embedding", return_value=[0.1] * 768)
def test_retrieve_vector_only(mock_embed):
    """Vector search works without neo4j."""
    chroma = MagicMock()
    chroma.search.return_value = [_make_search_result()]

    result = retrieve("test query", chroma, neo4j=None, top_k=3)

    assert isinstance(result, RetrievalResult)
    assert len(result.vector_results) == 1
    assert result.graph_context == ""
    chroma.search.assert_called_once()


@patch("src.rag.retriever.get_single_embedding", return_value=[0.1] * 768)
@patch("src.rag.retriever.get_graph_context", return_value="'Policy' is related to: VPN")
@patch("src.rag.retriever.extract_entities_from_query", return_value=["Policy"])
def test_retrieve_hybrid_with_graph(mock_entities, mock_graph_ctx, mock_embed):
    """When neo4j is provided, result includes graph context."""
    chroma = MagicMock()
    chroma.search.return_value = [_make_search_result()]
    neo4j = MagicMock()

    result = retrieve("policy question", chroma, neo4j, top_k=3)

    assert result.graph_context == "'Policy' is related to: VPN"
    mock_entities.assert_called_once_with("policy question", neo4j)


@patch("src.rag.retriever.get_single_embedding", return_value=[0.1] * 768)
@patch("src.rag.retriever.extract_entities_from_query", side_effect=RuntimeError("Neo4j down"))
def test_retrieve_graph_failure_degrades_gracefully(mock_entities, mock_embed):
    """Graph failure should not crash the retrieval."""
    chroma = MagicMock()
    chroma.search.return_value = [_make_search_result()]
    neo4j = MagicMock()

    result = retrieve("query", chroma, neo4j, top_k=3)

    assert len(result.vector_results) == 1
    assert result.graph_context == ""


@patch("src.rag.retriever.get_single_embedding", return_value=[0.1] * 768)
def test_retrieve_empty_results(mock_embed):
    """Empty vector results should return cleanly."""
    chroma = MagicMock()
    chroma.search.return_value = []

    result = retrieve("nothing here", chroma, neo4j=None, top_k=5)

    assert result.vector_results == []
    assert result.graph_context == ""
