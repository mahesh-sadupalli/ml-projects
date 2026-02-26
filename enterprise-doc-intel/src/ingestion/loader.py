from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A loaded document with its content and metadata."""

    content: str
    metadata: dict = field(default_factory=dict)


def load_text(path: Path) -> Document:
    return Document(
        content=path.read_text(encoding="utf-8"),
        metadata={"source": str(path), "type": "text"},
    )


def load_markdown(path: Path) -> Document:
    return Document(
        content=path.read_text(encoding="utf-8"),
        metadata={"source": str(path), "type": "markdown"},
    )


def load_pdf(path: Path) -> Document:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pypdf is required to load PDF files. Install dependencies with `pip install -e .`."
        ) from exc

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return Document(
        content="\n\n".join(pages),
        metadata={"source": str(path), "type": "pdf", "pages": len(reader.pages)},
    )


LOADERS = {
    ".txt": load_text,
    ".md": load_markdown,
    ".pdf": load_pdf,
}


def load_directory(directory: str | Path) -> list[Document]:
    """Load all supported documents from a directory recursively."""
    directory = Path(directory)
    documents: list[Document] = []

    for path in sorted(directory.rglob("*")):
        suffix = path.suffix.lower()
        if path.is_file() and suffix in LOADERS:
            try:
                doc = LOADERS[suffix](path)
                documents.append(doc)
                logger.info("Loaded %s (%d chars)", path.name, len(doc.content))
            except Exception:
                logger.exception("Failed to load %s", path)

    logger.info("Loaded %d documents from %s", len(documents), directory)
    return documents
