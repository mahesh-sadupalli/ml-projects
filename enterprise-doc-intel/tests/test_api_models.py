import pytest
from pydantic import ValidationError

from src.api.models import HealthResponse, IngestRequest, QueryRequest, QueryResponse, SourceInfo


def test_query_request_rejects_invalid_mode():
    with pytest.raises(ValidationError):
        QueryRequest(question="What is the policy?", mode="invalid")


def test_query_response_list_defaults_are_isolated():
    first = QueryResponse(answer="A", mode="rag")
    second = QueryResponse(answer="B", mode="rag")

    first.sources.append(SourceInfo(source="doc-a.md", score=0.9))
    first.agent_steps.append({"tool": "search_documents"})

    assert second.sources == []
    assert second.agent_steps == []


def test_query_request_rejects_empty_question():
    with pytest.raises(ValidationError):
        QueryRequest(question="", mode="rag")


def test_query_request_rejects_top_k_out_of_range():
    with pytest.raises(ValidationError):
        QueryRequest(question="q", top_k=0)
    with pytest.raises(ValidationError):
        QueryRequest(question="q", top_k=21)


def test_query_request_defaults():
    req = QueryRequest(question="What?")
    assert req.mode == "rag"
    assert req.top_k == 5


def test_ingest_request_default():
    req = IngestRequest()
    assert req.data_dir == "./data/sample_docs"


def test_health_response_defaults():
    resp = HealthResponse(status="ok")
    assert resp.chroma_docs == 0
    assert resp.neo4j_connected is False
