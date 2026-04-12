"""Unit tests for the RAG context builder."""

from __future__ import annotations

from src.rag.context_builder import build_context, build_prompt
from src.rag.retriever import RetrievalResult
from src.vectorstore.chroma import SearchResult


def _make_result(text="chunk", source="doc.md", score=0.9):
    return SearchResult(id="c1", text=text, metadata={"source": source}, score=score)


def test_build_context_with_vector_results():
    retrieval = RetrievalResult(
        vector_results=[_make_result(text="Policy text", source="policy.md", score=0.85)],
        graph_context="",
    )
    context = build_context(retrieval)

    assert "[Source 1: policy.md (relevance: 0.850)]" in context
    assert "Policy text" in context


def test_build_context_with_graph_context():
    retrieval = RetrievalResult(
        vector_results=[_make_result()],
        graph_context="'VPN' is related to: IT Team",
    )
    context = build_context(retrieval)

    assert "## Knowledge Graph Context" in context
    assert "'VPN' is related to: IT Team" in context


def test_build_context_empty_retrieval():
    retrieval = RetrievalResult(vector_results=[], graph_context="")
    context = build_context(retrieval)
    assert context == ""


def test_build_prompt_includes_question_and_context():
    prompt = build_prompt("What is the policy?", "Some context here.")

    assert "What is the policy?" in prompt
    assert "Some context here." in prompt
    assert "[Source N]" in prompt
