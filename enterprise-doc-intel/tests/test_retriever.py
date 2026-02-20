"""Integration test stubs for the retriever — require Ollama and ChromaDB running."""

import pytest


@pytest.mark.skip(reason="Requires Ollama running locally")
class TestRetriever:
    def test_vector_search_returns_results(self):
        """After ingestion, vector search should return relevant chunks."""
        pass

    def test_hybrid_search_includes_graph_context(self):
        """When Neo4j is available, results should include graph context."""
        pass

    def test_retriever_graceful_without_neo4j(self):
        """Retriever should work with ChromaDB alone when Neo4j is unavailable."""
        pass
