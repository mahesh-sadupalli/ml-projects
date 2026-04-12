from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.models import IngestRequest, IngestResponse
from src.ingestion.pipeline import run_pipeline

router = APIRouter()

# Ingestion is restricted to paths under this directory.
_ALLOWED_ROOT = Path("./data").resolve()


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    target = Path(request.data_dir).resolve()
    if not target.is_relative_to(_ALLOWED_ROOT):
        raise HTTPException(status_code=400, detail="data_dir must be inside ./data/")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="data_dir does not exist or is not a directory")
    summary = run_pipeline(data_dir=request.data_dir)
    return IngestResponse(**summary)
