"""Ingestion pipeline: load documents → chunk → embed → store in vector DB + knowledge graph."""

from __future__ import annotations

import hashlib
import logging

from src.config import settings
from src.embeddings.provider import get_embeddings
from src.ingestion.chunker import chunk_text
from src.ingestion.loader import load_directory
from src.knowledge_graph.extractor import extract_and_store
from src.knowledge_graph.neo4j_client import Neo4jClient
from src.vectorstore.chroma import ChromaStore

logger = logging.getLogger(__name__)


def _build_chunk_id(index: int, text: str, metadata: dict) -> str:
    source = metadata.get("source", "unknown")
    chunk_index = metadata.get("chunk_index", index)
    digest = hashlib.sha1(f"{source}|{chunk_index}|{text}".encode("utf-8")).hexdigest()[:16]
    return f"chunk_{digest}"


def run_pipeline(data_dir: str | None = None) -> dict:
    """Run the full ingestion pipeline.

    Returns a summary dict with counts of documents, chunks, and entities processed.
    """
    data_dir = data_dir or settings.data_dir

    # 1. Load documents
    logger.info("Loading documents from %s", data_dir)
    documents = load_directory(data_dir)

    if not documents:
        logger.warning("No documents found in %s", data_dir)
        return {"documents": 0, "chunks": 0, "entities": 0}

    # 2. Chunk documents
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(
            doc.content,
            strategy="recursive",
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
            metadata=doc.metadata,
        )
        all_chunks.extend(chunks)

    logger.info("Created %d chunks from %d documents", len(all_chunks), len(documents))

    # 3. Generate embeddings and store in ChromaDB
    if all_chunks:
        chroma = ChromaStore()
        texts = [c.text for c in all_chunks]
        metadatas = [c.metadata for c in all_chunks]
        ids = [_build_chunk_id(i, c.text, c.metadata) for i, c in enumerate(all_chunks)]

        embeddings = get_embeddings(texts)
        chroma.add(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
        logger.info("Stored %d chunks in ChromaDB", len(all_chunks))
    else:
        logger.warning("No non-empty chunks generated; skipping vector storage")

    # 4. Extract entities/relations and store in Neo4j
    entity_count = 0
    try:
        neo4j = Neo4jClient()
        for doc in documents:
            count = extract_and_store(doc.content, doc.metadata, neo4j)
            entity_count += count
        neo4j.close()
        logger.info("Extracted %d entities into Neo4j", entity_count)
    except Exception:
        logger.exception("Knowledge graph extraction failed (Neo4j may not be running)")

    summary = {
        "documents": len(documents),
        "chunks": len(all_chunks),
        "entities": entity_count,
    }
    logger.info("Pipeline complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    run_pipeline()
