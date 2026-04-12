"""Unit tests for agent planner, tools, and orchestrator (mocked Ollama + stores)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.agents.orchestrator import AgentResult, run_agent
from src.agents.planner import decompose_query
from src.agents.tools import build_tools, compare_documents, search_documents, summarize
from src.vectorstore.chroma import SearchResult


def _make_search_result(text: str = "chunk", source: str = "doc.md", score: float = 0.9) -> SearchResult:
    return SearchResult(id="c1", text=text, metadata={"source": source}, score=score)


# --- Planner tests ---


@patch("src.agents.planner.ollama_client")
def test_decompose_query_parses_valid_plan(mock_ollama):
    mock_ollama.chat.return_value = {
        "message": {
            "content": '{"steps": [{"tool": "search_documents", "input": "VPN policy", "reason": "find VPN info"}]}'
        }
    }

    steps = decompose_query("What is the VPN policy?", "- search_documents: Search docs")

    assert len(steps) == 1
    assert steps[0]["tool"] == "search_documents"


@patch("src.agents.planner.ollama_client")
def test_decompose_query_falls_back_on_bad_json(mock_ollama):
    mock_ollama.chat.return_value = {"message": {"content": "Not valid json at all"}}

    steps = decompose_query("question", "tools")

    assert len(steps) == 1
    assert steps[0]["tool"] == "search_documents"


@patch("src.agents.planner.ollama_client")
def test_decompose_query_falls_back_on_ollama_failure(mock_ollama):
    mock_ollama.chat.side_effect = ConnectionError("unreachable")

    steps = decompose_query("question", "tools")

    assert len(steps) == 1
    assert steps[0]["tool"] == "search_documents"
    assert "planner unavailable" in steps[0]["reason"]


# --- Tools tests ---


def test_search_documents_formats_results():
    chroma = MagicMock()
    retrieval_mock = MagicMock()
    retrieval_mock.vector_results = [_make_search_result(text="Policy text", source="policy.md")]
    retrieval_mock.graph_context = ""

    with patch("src.agents.tools.retrieve", return_value=retrieval_mock):
        result = search_documents("policy", chroma=chroma)

    assert "policy.md" in result
    assert "Policy text" in result


def test_search_documents_returns_message_on_no_results():
    chroma = MagicMock()
    retrieval_mock = MagicMock()
    retrieval_mock.vector_results = []

    with patch("src.agents.tools.retrieve", return_value=retrieval_mock):
        result = search_documents("nothing", chroma=chroma)

    assert "No relevant documents found" in result


@patch("src.agents.tools.ollama_client")
def test_summarize_returns_llm_output(mock_ollama):
    mock_ollama.chat.return_value = {"message": {"content": "Brief summary."}}

    result = summarize("Long text here...")

    assert result == "Brief summary."


@patch("src.agents.tools.ollama_client")
def test_summarize_handles_ollama_failure(mock_ollama):
    mock_ollama.chat.side_effect = ConnectionError("down")

    result = summarize("text")

    assert "unavailable" in result.lower()


def test_compare_documents_groups_by_source():
    retrieval_mock = MagicMock()
    retrieval_mock.vector_results = [
        _make_search_result(text="chunk A", source="doc1.md"),
        _make_search_result(text="chunk B", source="doc2.md"),
    ]

    with patch("src.agents.tools.retrieve", return_value=retrieval_mock):
        result = compare_documents("compare", chroma=MagicMock())

    assert "doc1.md" in result
    assert "doc2.md" in result


def test_build_tools_without_neo4j():
    tools = build_tools(MagicMock(), neo4j=None)
    names = {t.name for t in tools}
    assert "search_documents" in names
    assert "summarize" in names
    assert "compare_documents" in names
    assert "query_knowledge_graph" not in names


def test_build_tools_with_neo4j():
    tools = build_tools(MagicMock(), neo4j=MagicMock())
    names = {t.name for t in tools}
    assert "query_knowledge_graph" in names


# --- Orchestrator tests ---


@patch("src.agents.orchestrator.ollama_client")
@patch("src.agents.orchestrator.decompose_query")
def test_run_agent_returns_answer_with_steps(mock_decompose, mock_ollama):
    mock_decompose.return_value = [
        {"tool": "search_documents", "input": "VPN policy", "reason": "find info"}
    ]
    mock_ollama.chat.return_value = {"message": {"content": "The VPN policy requires..."}}

    chroma = MagicMock()
    retrieval_mock = MagicMock()
    retrieval_mock.vector_results = [_make_search_result()]
    retrieval_mock.graph_context = ""

    with patch("src.agents.tools.retrieve", return_value=retrieval_mock):
        result = run_agent("What is the VPN policy?", chroma, neo4j=None)

    assert isinstance(result, AgentResult)
    assert result.answer != ""
    assert len(result.steps) == 1
    assert result.steps[0].tool == "search_documents"


@patch("src.agents.orchestrator.ollama_client")
@patch("src.agents.orchestrator.decompose_query")
def test_run_agent_handles_unknown_tool(mock_decompose, mock_ollama):
    mock_decompose.return_value = [
        {"tool": "nonexistent_tool", "input": "x", "reason": "bad plan"}
    ]
    mock_ollama.chat.return_value = {"message": {"content": "Answer despite bad tool."}}

    result = run_agent("question", MagicMock(), neo4j=None)

    assert "Unknown tool" in result.steps[0].observation


@patch("src.agents.orchestrator.ollama_client")
@patch("src.agents.orchestrator.decompose_query")
def test_run_agent_synthesis_failure_returns_fallback(mock_decompose, mock_ollama):
    mock_decompose.return_value = [
        {"tool": "search_documents", "input": "q", "reason": "search"}
    ]
    # First call for synthesis fails
    mock_ollama.chat.side_effect = ConnectionError("down")

    chroma = MagicMock()
    retrieval_mock = MagicMock()
    retrieval_mock.vector_results = [_make_search_result()]
    retrieval_mock.graph_context = ""

    with patch("src.agents.tools.retrieve", return_value=retrieval_mock):
        result = run_agent("question", chroma, neo4j=None)

    assert "could not generate" in result.answer.lower()
