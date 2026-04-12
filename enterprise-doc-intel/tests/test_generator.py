"""Unit tests for the RAG generator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.rag.generator import GenerationResult, generate_answer
from src.rag.retriever import RetrievalResult
from src.vectorstore.chroma import SearchResult


def _make_retrieval():
    return RetrievalResult(
        vector_results=[
            SearchResult(id="c1", text="chunk", metadata={"source": "doc.md"}, score=0.9),
        ],
        graph_context="",
    )


@patch("src.rag.generator.ollama_client")
@patch("src.rag.generator.retrieve", return_value=_make_retrieval())
def test_generate_answer_returns_result(mock_retrieve, mock_ollama):
    mock_ollama.chat.return_value = {"message": {"content": "The answer is 42."}}

    result = generate_answer("question", MagicMock())

    assert isinstance(result, GenerationResult)
    assert result.answer == "The answer is 42."
    assert len(result.sources) == 1
    assert result.sources[0]["source"] == "doc.md"


@patch("src.rag.generator.ollama_client")
@patch("src.rag.generator.retrieve", return_value=_make_retrieval())
def test_generate_answer_raises_on_ollama_failure(mock_retrieve, mock_ollama):
    mock_ollama.chat.side_effect = ConnectionError("down")

    try:
        generate_answer("question", MagicMock())
        assert False, "Should have raised"
    except RuntimeError as e:
        assert "LLM generation failed" in str(e)
