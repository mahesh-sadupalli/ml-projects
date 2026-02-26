from fastapi import APIRouter

from src.api.models import HealthResponse
from src.vectorstore.chroma import ChromaStore

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    status = "ok"
    chroma_docs = 0
    neo4j_connected = False

    try:
        chroma = ChromaStore()
        chroma_docs = chroma.count
    except Exception:
        status = "degraded"

    try:
        from src.knowledge_graph.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client.close()
        neo4j_connected = True
    except Exception:
        status = "degraded"

    return HealthResponse(status=status, chroma_docs=chroma_docs, neo4j_connected=neo4j_connected)
