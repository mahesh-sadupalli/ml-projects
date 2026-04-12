"""Unit tests for knowledge graph extraction and query (mocked Ollama + Neo4j)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.knowledge_graph.extractor import extract_and_store, extract_entities_and_relations
from src.knowledge_graph.query import extract_entities_from_query, get_graph_context


# --- Extractor tests ---


@patch("src.knowledge_graph.extractor.ollama_client")
def test_extract_entities_parses_valid_json(mock_ollama):
    mock_ollama.chat.return_value = {
        "message": {
            "content": '{"entities": [{"name": "VPN", "label": "Technology"}], "relationships": []}'
        }
    }

    result = extract_entities_and_relations("We use a VPN for remote access.")

    assert len(result["entities"]) == 1
    assert result["entities"][0]["name"] == "VPN"


@patch("src.knowledge_graph.extractor.ollama_client")
def test_extract_entities_handles_markdown_wrapped_json(mock_ollama):
    mock_ollama.chat.return_value = {
        "message": {
            "content": '```json\n{"entities": [{"name": "IT", "label": "Organization"}], "relationships": []}\n```'
        }
    }

    result = extract_entities_and_relations("Contact IT for support.")

    assert len(result["entities"]) == 1


@patch("src.knowledge_graph.extractor.ollama_client")
def test_extract_entities_returns_empty_on_bad_json(mock_ollama):
    mock_ollama.chat.return_value = {"message": {"content": "Sorry, I cannot extract entities."}}

    result = extract_entities_and_relations("Some text.")

    assert result == {"entities": [], "relationships": []}


def test_extract_entities_skips_empty_text():
    result = extract_entities_and_relations("")
    assert result == {"entities": [], "relationships": []}

    result = extract_entities_and_relations("   ")
    assert result == {"entities": [], "relationships": []}


@patch("src.knowledge_graph.extractor.ollama_client")
def test_extract_entities_handles_ollama_failure(mock_ollama):
    mock_ollama.chat.side_effect = ConnectionError("Ollama unreachable")

    result = extract_entities_and_relations("Some text.")

    assert result == {"entities": [], "relationships": []}


@patch("src.knowledge_graph.extractor.extract_entities_and_relations")
def test_extract_and_store_creates_entities(mock_extract):
    mock_extract.return_value = {
        "entities": [
            {"name": "VPN", "label": "Technology"},
            {"name": "IT Team", "label": "Organization"},
        ],
        "relationships": [
            {"from": "IT Team", "to": "VPN", "type": "USES"},
        ],
    }
    neo4j = MagicMock()

    count = extract_and_store("text", {"source": "doc.md", "type": "markdown"}, neo4j)

    assert count == 2
    # Document node + 2 entities = 3 create_entity calls
    assert neo4j.create_entity.call_count == 3
    # 2 MENTIONS + 1 explicit relationship = 3
    assert neo4j.create_relationship.call_count == 3


@patch("src.knowledge_graph.extractor.extract_entities_and_relations")
def test_extract_and_store_skips_empty_names(mock_extract):
    mock_extract.return_value = {
        "entities": [{"name": "", "label": "Concept"}, {"name": "  ", "label": "Concept"}],
        "relationships": [],
    }
    neo4j = MagicMock()

    count = extract_and_store("text", {"source": "doc.md"}, neo4j)

    assert count == 2  # raw entity count from LLM response
    # Only the Document node, no entity nodes for empty names
    assert neo4j.create_entity.call_count == 1


# --- Query tests ---


def test_extract_entities_from_query_finds_matches():
    neo4j = MagicMock()
    neo4j.get_all_entities.return_value = [
        {"name": "Data Security Policy", "labels": ["Policy"]},
        {"name": "VPN", "labels": ["Technology"]},
        {"name": "IT", "labels": ["Organization"]},
    ]

    found = extract_entities_from_query("What is the data security policy?", neo4j)

    assert "Data Security Policy" in found


def test_extract_entities_from_query_returns_empty_on_no_match():
    neo4j = MagicMock()
    neo4j.get_all_entities.return_value = [
        {"name": "Remote Work Policy", "labels": ["Policy"]},
    ]

    found = extract_entities_from_query("What is the weather?", neo4j)

    assert found == []


def test_get_graph_context_builds_text():
    neo4j = MagicMock()
    neo4j.search_entities.return_value = [{"name": "VPN", "labels": ["Technology"]}]
    neo4j.get_neighbors.return_value = [
        {"name": "IT Team", "labels": ["Organization"], "distance": 1},
    ]

    context = get_graph_context(["VPN"], neo4j)

    assert "VPN" in context
    assert "IT Team" in context


def test_get_graph_context_returns_empty_on_no_entities():
    neo4j = MagicMock()
    neo4j.search_entities.return_value = []

    context = get_graph_context(["nonexistent"], neo4j)

    assert context == ""
