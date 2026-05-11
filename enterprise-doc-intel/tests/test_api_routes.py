"""HTTP-level tests for API routes using FastAPI TestClient."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import graph, health, ingest, query


def _make_app(chroma=None, neo4j=None) -> FastAPI:
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        app.state.chroma = chroma or MagicMock()
        app.state.neo4j = neo4j
        yield

    app = FastAPI(lifespan=_lifespan)
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(graph.router)
    return app


# --- Health ---


def test_health_returns_ok():
    chroma = MagicMock()
    chroma.count = 42
    with TestClient(_make_app(chroma=chroma, neo4j=MagicMock())) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["chroma_docs"] == 42
    assert resp.json()["neo4j_connected"] is True


def test_health_degraded_without_neo4j():
    chroma = MagicMock()
    chroma.count = 0
    with TestClient(_make_app(chroma=chroma, neo4j=None)) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"
    assert resp.json()["neo4j_connected"] is False


# --- Ingest ---


def test_ingest_rejects_path_traversal():
    with TestClient(_make_app()) as client:
        resp = client.post("/ingest", json={"data_dir": "/etc/passwd"})
    assert resp.status_code == 400
    assert "inside ./data/" in resp.json()["detail"]


def test_ingest_rejects_nonexistent_dir():
    with TestClient(_make_app()) as client:
        resp = client.post("/ingest", json={"data_dir": "./data/nonexistent_dir_xyz"})
    assert resp.status_code == 400


# --- Query ---


@patch("src.api.routes.query.generate_answer")
def test_query_rag_mode(mock_gen):
    from src.rag.generator import GenerationResult

    mock_gen.return_value = GenerationResult(
        answer="The policy says...",
        sources=[{"source": "policy.md", "score": 0.9}],
        graph_context="",
    )
    with TestClient(_make_app(neo4j=None)) as client:
        resp = client.post("/query", json={"question": "What is the policy?", "mode": "rag"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "rag"
    assert "policy" in resp.json()["answer"].lower()


@patch("src.api.routes.query.run_agent")
def test_query_agent_mode(mock_agent):
    from src.agents.orchestrator import AgentResult, AgentStep

    mock_agent.return_value = AgentResult(
        answer="Based on research...",
        steps=[AgentStep(thought="search", tool="search_documents", tool_input="q", observation="found it")],
    )
    with TestClient(_make_app(neo4j=None)) as client:
        resp = client.post("/query", json={"question": "Compare policies", "mode": "agent"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "agent"
    assert len(resp.json()["agent_steps"]) == 1


def test_query_rejects_empty_question():
    with TestClient(_make_app()) as client:
        resp = client.post("/query", json={"question": "", "mode": "rag"})
    assert resp.status_code == 422


# --- Graph ---


def test_graph_entities_returns_503_without_neo4j():
    with TestClient(_make_app(neo4j=None)) as client:
        resp = client.get("/graph/entities")
    assert resp.status_code == 503


def test_graph_neighbors_returns_503_without_neo4j():
    with TestClient(_make_app(neo4j=None)) as client:
        resp = client.get("/graph/neighbors/VPN")
    assert resp.status_code == 503


def test_graph_neighbors_validates_max_hops():
    with TestClient(_make_app(neo4j=MagicMock())) as client:
        resp = client.get("/graph/neighbors/VPN?max_hops=100")
    assert resp.status_code == 422
