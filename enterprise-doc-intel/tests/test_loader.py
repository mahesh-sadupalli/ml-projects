import tempfile
from pathlib import Path

from src.ingestion.loader import load_directory, load_markdown, load_text


class TestLoaders:
    def test_load_text(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("Hello, world!")
        doc = load_text(f)
        assert doc.content == "Hello, world!"
        assert doc.metadata["type"] == "text"

    def test_load_markdown(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nContent here.")
        doc = load_markdown(f)
        assert "# Title" in doc.content
        assert doc.metadata["type"] == "markdown"

    def test_load_directory(self, tmp_path: Path):
        (tmp_path / "a.md").write_text("Document A")
        (tmp_path / "b.txt").write_text("Document B")
        (tmp_path / "c.csv").write_text("not,supported")  # should be skipped

        docs = load_directory(tmp_path)
        assert len(docs) == 2
        names = {Path(d.metadata["source"]).name for d in docs}
        assert names == {"a.md", "b.txt"}

    def test_load_empty_directory(self, tmp_path: Path):
        docs = load_directory(tmp_path)
        assert docs == []
