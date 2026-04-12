"""FastAPI application — Enterprise Document Intelligence Platform."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import graph, health, ingest, query
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage shared client instances across the app lifetime."""
    # Startup: create shared clients
    application.state.chroma = ChromaStore()
    logger.info("ChromaDB client initialized")

    try:
        application.state.neo4j = Neo4jClient()
        logger.info("Neo4j client initialized")
    except Exception:
        application.state.neo4j = None
        logger.warning("Neo4j not available, proceeding without knowledge graph")

    yield

    # Shutdown: clean up
    if application.state.neo4j is not None:
        application.state.neo4j.close()
        logger.info("Neo4j client closed")


app = FastAPI(
    title="Enterprise Document Intelligence",
    description="RAG + Knowledge Graphs + Agentic Workflows — from scratch",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(graph.router)
