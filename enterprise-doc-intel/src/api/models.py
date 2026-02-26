"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    data_dir: str = Field(default="./data/sample_docs", description="Directory containing documents to ingest")


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    entities: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask")
    mode: Literal["rag", "agent"] = Field(
        default="rag",
        description="Query mode: 'rag' for simple retrieval, 'agent' for multi-step reasoning",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")


class SourceInfo(BaseModel):
    source: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    mode: str
    sources: list[SourceInfo] = Field(default_factory=list)
    graph_context: str = ""
    agent_steps: list[dict] = Field(default_factory=list)


class EntityResponse(BaseModel):
    name: str
    labels: list[str]


class NeighborResponse(BaseModel):
    name: str
    labels: list[str]
    distance: int


class GraphNodeResponse(BaseModel):
    id: str
    name: str
    labels: list[str]


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    type: str


class GraphSubgraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class HealthResponse(BaseModel):
    status: str
    chroma_docs: int = 0
    neo4j_connected: bool = False
