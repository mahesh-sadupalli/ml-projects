"""FastAPI application — Enterprise Document Intelligence Platform."""

import logging

from fastapi import FastAPI

from src.api.routes import graph, health, ingest, query

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

app = FastAPI(
    title="Enterprise Document Intelligence",
    description="RAG + Knowledge Graphs + Agentic Workflows — from scratch",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(graph.router)
