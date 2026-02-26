import pytest

pytest.importorskip("neo4j")

from src.knowledge_graph.neo4j_client import Neo4jClient


def _mock_client(responses: list[list[dict]]):
    client = object.__new__(Neo4jClient)
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
