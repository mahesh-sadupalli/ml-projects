import pytest
from pydantic import ValidationError

from src.api.models import QueryRequest, QueryResponse, SourceInfo


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
