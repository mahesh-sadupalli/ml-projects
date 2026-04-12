"""Embedding provider using Ollama's local embedding models."""

from __future__ import annotations

import logging

import ollama as ollama_client

from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    """Raised when Ollama embedding fails."""


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama.

    Uses the model specified in settings.ollama_embed_model (default: nomic-embed-text).
    Raises EmbeddingError on network or model failures.
    """
    embeddings: list[list[float]] = []

    for text in texts:
        try:
            response = ollama_client.embed(
                model=settings.ollama_embed_model,
                input=text,
            )
            embeddings.append(response["embeddings"][0])
        except Exception as exc:
            raise EmbeddingError(
                f"Ollama embedding failed (model={settings.ollama_embed_model}): {exc}"
            ) from exc

    logger.info("Generated %d embeddings via %s", len(embeddings), settings.ollama_embed_model)
    return embeddings


def get_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text. Raises EmbeddingError on failure."""
    try:
        response = ollama_client.embed(
            model=settings.ollama_embed_model,
            input=text,
        )
        return response["embeddings"][0]
    except Exception as exc:
        raise EmbeddingError(
            f"Ollama embedding failed (model={settings.ollama_embed_model}): {exc}"
        ) from exc
