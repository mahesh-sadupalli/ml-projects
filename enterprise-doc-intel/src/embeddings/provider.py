"""Embedding provider using Ollama's local embedding models."""

from __future__ import annotations

import logging

import ollama as ollama_client

from src.config import settings

logger = logging.getLogger(__name__)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama.

    Uses the model specified in settings.ollama_embed_model (default: nomic-embed-text).
    """
    embeddings: list[list[float]] = []

    for text in texts:
        response = ollama_client.embed(
            model=settings.ollama_embed_model,
            input=text,
        )
        embeddings.append(response["embeddings"][0])

    logger.info("Generated %d embeddings via %s", len(embeddings), settings.ollama_embed_model)
    return embeddings


def get_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text."""
    response = ollama_client.embed(
        model=settings.ollama_embed_model,
        input=text,
    )
    return response["embeddings"][0]
