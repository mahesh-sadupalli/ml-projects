import pytest

pytest.importorskip("neo4j")

from src.knowledge_graph.neo4j_client import Neo4jClient, _safe_identifier


def _mock_client(responses: list[list[dict]] | None = None):
    client = object.__new__(Neo4jClient)
    if responses is not None:
        sequence = iter(responses)

        def fake_run_query(_cypher: str, _params: dict | None = None):
            return next(sequence)

        client.run_query = fake_run_query  # type: ignore[method-assign]
    return client


def test_get_subgraph_returns_empty_for_missing_entity():
    client = _mock_client([[]])
    result = client.get_subgraph("missing")
    assert result == {"nodes": [], "edges": []}


def test_get_subgraph_keeps_start_node_when_no_paths():
    client = _mock_client(
        [
            [{"id": "1", "name": "root", "labels": ["Concept"]}],
            [],
            [],
        ]
    )
    result = client.get_subgraph("root")
    assert result["nodes"] == [{"id": "1", "name": "root", "labels": ["Concept"]}]
    assert result["edges"] == []


def test_get_subgraph_inserts_start_node_if_not_present():
    client = _mock_client(
        [
            [{"id": "1", "name": "root", "labels": ["Concept"]}],
            [{"id": "2", "name": "child", "labels": ["Concept"]}],
            [{"source": "1", "target": "2", "type": "RELATES_TO"}],
        ]
    )
    result = client.get_subgraph("root")
    assert result["nodes"][0]["id"] == "1"
    assert any(node["id"] == "2" for node in result["nodes"])


# --- _safe_identifier tests ---


def test_safe_identifier_valid_label():
    from src.knowledge_graph.neo4j_client import _ALLOWED_LABELS
    assert _safe_identifier("Policy", "Concept", _ALLOWED_LABELS) == "Policy"


def test_safe_identifier_invalid_label_falls_back():
    from src.knowledge_graph.neo4j_client import _ALLOWED_LABELS
    assert _safe_identifier("InvalidLabel", "Concept", _ALLOWED_LABELS) == "Concept"


def test_safe_identifier_invalid_characters_falls_back():
    assert _safe_identifier("DROP TABLE;", "Concept", None) == "Concept"


def test_safe_identifier_spaces_replaced():
    from src.knowledge_graph.neo4j_client import _ALLOWED_REL_TYPES
    assert _safe_identifier("PART OF", "RELATES_TO", _ALLOWED_REL_TYPES) == "PART_OF"


# --- create_entity / create_relationship with mock ---


def test_create_entity_uses_safe_label():
    calls = []
    client = _mock_client()
    client.run_query = lambda cypher, params=None: calls.append((cypher, params)) or []

    client.create_entity("InvalidLabel", "Test Entity")
    # Should fall back to Concept
    assert "Concept" in calls[0][0]


def test_create_relationship_falls_back_on_invalid_rel_type():
    calls = []
    client = _mock_client()
    client.run_query = lambda cypher, params=None: calls.append((cypher, params)) or []

    client.create_relationship("Concept", "A", "Concept", "B", "INVALID_TYPE")
    assert "RELATES_TO" in calls[0][0]
