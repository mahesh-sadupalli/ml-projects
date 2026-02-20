"""ChromaDB vector store wrapper."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import chromadb

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from the vector store."""

    text: str
    metadata: dict
    score: float
    id: str


class ChromaStore:
    """Wrapper around ChromaDB for document storage and retrieval."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add documents with pre-computed embeddings."""
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Upserted %d documents (total: %d)", len(ids), self.count)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents by embedding vector."""
        kwargs: dict = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        search_results: list[SearchResult] = []
        for i in range(len(results["ids"][0])):
            search_results.append(
                SearchResult(
                    id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1 - results["distances"][0][i],  # cosine distance → similarity
                )
            )

        return search_results

    def reset(self) -> None:
        """Delete and recreate the collection."""
        self._client.delete_collection(settings.chroma_collection)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
