"""Integration test stubs for the knowledge graph — require Neo4j running."""

import pytest


@pytest.mark.skip(reason="Requires Neo4j running via Docker")
class TestKnowledgeGraph:
    def test_create_and_retrieve_entity(self):
        """Should create an entity and retrieve it by name."""
        pass

    def test_create_relationship(self):
        """Should create a relationship between two entities."""
        pass

    def test_get_neighbors(self):
        """Should return neighbors within N hops."""
        pass

    def test_entity_search(self):
        """Case-insensitive entity search should find matches."""
        pass
