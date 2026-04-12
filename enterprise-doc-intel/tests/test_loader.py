from pathlib import Path

from src.ingestion.loader import Document, load_directory, load_markdown, load_pdf, load_text


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

    def test_load_directory_case_insensitive_extensions(self, tmp_path: Path):
        (tmp_path / "policy.MD").write_text("Policy Document")
        (tmp_path / "readme.TXT").write_text("Readme Document")

        docs = load_directory(tmp_path)
        names = {Path(d.metadata["source"]).name for d in docs}
        assert names == {"policy.MD", "readme.TXT"}

    def test_load_empty_directory(self, tmp_path: Path):
        docs = load_directory(tmp_path)
        assert docs == []

    def test_load_pdf(self, tmp_path: Path):
        """PDF loading via pypdf."""
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        doc = load_pdf(pdf_path)
        assert doc.metadata["type"] == "pdf"
        assert doc.metadata["pages"] == 1

    def test_load_directory_skips_unreadable_files(self, tmp_path: Path):
        """A file that fails to load should be skipped, not crash the pipeline."""
        good = tmp_path / "good.txt"
        good.write_text("good content")
        bad = tmp_path / "bad.txt"
        bad.write_text("content")
        bad.chmod(0o000)  # make unreadable

        docs = load_directory(tmp_path)
        # Should get at least the good file; bad file is skipped
        sources = [d.metadata["source"] for d in docs]
        assert str(good) in sources

        bad.chmod(0o644)  # restore for cleanup

    def test_load_directory_with_subdirectories(self, tmp_path: Path):
        """Should recursively find files in subdirectories."""
        sub = tmp_path / "policies"
        sub.mkdir()
        (sub / "policy.md").write_text("Policy content")
        (tmp_path / "readme.txt").write_text("Readme")

        docs = load_directory(tmp_path)
        assert len(docs) == 2
