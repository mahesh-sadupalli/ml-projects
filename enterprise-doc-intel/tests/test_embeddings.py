"""Unit tests for the embedding provider."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.embeddings.provider import EmbeddingError, get_embeddings, get_single_embedding


@patch("src.embeddings.provider.ollama_client")
def test_get_embeddings_returns_vectors(mock_ollama):
    mock_ollama.embed.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}

    result = get_embeddings(["hello", "world"])

    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]


@patch("src.embeddings.provider.ollama_client")
def test_get_embeddings_raises_on_failure(mock_ollama):
    mock_ollama.embed.side_effect = ConnectionError("down")

    with pytest.raises(EmbeddingError, match="Ollama embedding failed"):
        get_embeddings(["hello"])


@patch("src.embeddings.provider.ollama_client")
def test_get_single_embedding(mock_ollama):
    mock_ollama.embed.return_value = {"embeddings": [[0.5, 0.6]]}

    result = get_single_embedding("hello")

    assert result == [0.5, 0.6]


@patch("src.embeddings.provider.ollama_client")
def test_get_single_embedding_raises_on_failure(mock_ollama):
    mock_ollama.embed.side_effect = ConnectionError("unreachable")

    with pytest.raises(EmbeddingError):
        get_single_embedding("hello")
