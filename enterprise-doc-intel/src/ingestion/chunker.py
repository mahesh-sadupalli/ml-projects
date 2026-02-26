from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A text chunk with metadata tracing back to its source."""

    text: str
    metadata: dict = field(default_factory=dict)


def _normalize_chunk_params(chunk_size: int, overlap: int) -> int:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    # Cap overlap so the chunk cursor always moves forward.
    return min(overlap, chunk_size - 1)


def fixed_size_chunks(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Split text into fixed-size character chunks with overlap."""
    overlap = _normalize_chunk_params(chunk_size, overlap)
    metadata = metadata or {}
    chunks: list[Chunk] = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        if chunk_text.strip():
            chunks.append(
                Chunk(
                    text=chunk_text,
                    metadata={**metadata, "chunk_index": len(chunks), "strategy": "fixed"},
                )
            )

        start += step

    return chunks


_SEPARATORS = ["\n\n", "\n", ". ", " "]


def recursive_chunks(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    metadata: dict | None = None,
    _separators: list[str] | None = None,
) -> list[Chunk]:
    """Recursively split text using a hierarchy of separators.

    Tries the most meaningful separator first (paragraph break), then falls
    back to less meaningful ones (newline, sentence, word).
    """
    overlap = _normalize_chunk_params(chunk_size, overlap)
    metadata = metadata or {}
    separators = _separators if _separators is not None else list(_SEPARATORS)

    if len(text) <= chunk_size:
        if text.strip():
            return [
                Chunk(
                    text=text,
                    metadata={**metadata, "chunk_index": 0, "strategy": "recursive"},
                )
            ]
        return []

    # Find the best separator that actually exists in the text
    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    parts = text.split(separator) if separator else [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Merge small parts into chunk-sized groups
    chunks: list[Chunk] = []
    current = ""

    for part in parts:
        candidate = current + separator + part if current else part

        if len(candidate) > chunk_size and current:
            chunks.append(
                Chunk(
                    text=current.strip(),
                    metadata={**metadata, "chunk_index": len(chunks), "strategy": "recursive"},
                )
            )
            # Keep overlap from end of current chunk
            current = current[-overlap:] + separator + part if overlap else part
        else:
            current = candidate

    if current.strip():
        chunks.append(
            Chunk(
                text=current.strip(),
                metadata={**metadata, "chunk_index": len(chunks), "strategy": "recursive"},
            )
        )

    return chunks


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 512,
    overlap: int = 64,
    metadata: dict | None = None,
) -> list[Chunk]:
    """Chunk text using the specified strategy."""
    if strategy == "fixed":
        return fixed_size_chunks(text, chunk_size, overlap, metadata)
    elif strategy == "recursive":
        return recursive_chunks(text, chunk_size, overlap, metadata)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
