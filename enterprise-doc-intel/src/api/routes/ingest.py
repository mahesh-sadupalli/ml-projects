from fastapi import APIRouter

from src.api.models import IngestRequest, IngestResponse
from src.ingestion.pipeline import run_pipeline

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    summary = run_pipeline(data_dir=request.data_dir)
    return IngestResponse(**summary)
