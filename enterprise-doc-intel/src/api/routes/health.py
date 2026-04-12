from fastapi import APIRouter, Request

from src.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    chroma = request.app.state.chroma
    neo4j = request.app.state.neo4j

    try:
        chroma_docs = chroma.count
    except Exception:
        chroma_docs = 0

    neo4j_connected = neo4j is not None
    status = "ok" if chroma_docs >= 0 and neo4j_connected else "degraded"

    return HealthResponse(status=status, chroma_docs=chroma_docs, neo4j_connected=neo4j_connected)
