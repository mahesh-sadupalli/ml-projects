"""Unit tests for the ingestion pipeline (mocked dependencies)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.ingestion.pipeline import run_pipeline


@patch("src.ingestion.pipeline.Neo4jClient")
@patch("src.ingestion.pipeline.get_embeddings", return_value=[[0.1] * 768])
@patch("src.ingestion.pipeline.ChromaStore")
@patch("src.ingestion.pipeline.load_directory")
def test_pipeline_runs_end_to_end(mock_load, mock_chroma_cls, mock_embed, mock_neo4j_cls):
    from src.ingestion.loader import Document

    mock_load.return_value = [Document(content="Hello world", metadata={"source": "doc.txt", "type": "text"})]
    mock_chroma = MagicMock()
    mock_chroma_cls.return_value = mock_chroma
    mock_neo4j = MagicMock()
    mock_neo4j_cls.return_value = mock_neo4j

    with patch("src.ingestion.pipeline.extract_and_store", return_value=2):
        summary = run_pipeline(data_dir="./data/sample_docs")

    assert summary["documents"] == 1
    assert summary["chunks"] >= 1
    assert summary["entities"] == 2
    mock_chroma.add.assert_called_once()
    mock_neo4j.close.assert_called_once()


@patch("src.ingestion.pipeline.load_directory", return_value=[])
def test_pipeline_empty_directory(mock_load):
    summary = run_pipeline(data_dir="./data/empty")

    assert summary == {"documents": 0, "chunks": 0, "entities": 0}


@patch("src.ingestion.pipeline.Neo4jClient", side_effect=ConnectionError("Neo4j down"))
@patch("src.ingestion.pipeline.get_embeddings", return_value=[[0.1] * 768])
@patch("src.ingestion.pipeline.ChromaStore")
@patch("src.ingestion.pipeline.load_directory")
def test_pipeline_continues_without_neo4j(mock_load, mock_chroma_cls, mock_embed, mock_neo4j_cls):
    from src.ingestion.loader import Document

    mock_load.return_value = [Document(content="text", metadata={"source": "d.txt", "type": "text"})]
    mock_chroma_cls.return_value = MagicMock()

    summary = run_pipeline(data_dir="./data/sample_docs")

    assert summary["documents"] == 1
    assert summary["entities"] == 0  # KG extraction failed gracefully


@patch("src.ingestion.pipeline.Neo4jClient")
@patch("src.ingestion.pipeline.get_embeddings", return_value=[[0.1] * 768])
@patch("src.ingestion.pipeline.ChromaStore")
@patch("src.ingestion.pipeline.load_directory")
def test_pipeline_neo4j_closed_on_extraction_error(mock_load, mock_chroma_cls, mock_embed, mock_neo4j_cls):
    """Neo4j driver must be closed even if extraction raises mid-loop."""
    from src.ingestion.loader import Document

    mock_load.return_value = [Document(content="text", metadata={"source": "d.txt", "type": "text"})]
    mock_chroma_cls.return_value = MagicMock()
    mock_neo4j = MagicMock()
    mock_neo4j_cls.return_value = mock_neo4j

    with patch("src.ingestion.pipeline.extract_and_store", side_effect=RuntimeError("boom")):
        summary = run_pipeline(data_dir="./data/sample_docs")

    # Key assertion: close() called despite exception
    mock_neo4j.close.assert_called_once()
    assert summary["entities"] == 0
