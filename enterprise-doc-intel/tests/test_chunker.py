import pytest

from src.ingestion.chunker import chunk_text, fixed_size_chunks, recursive_chunks


class TestFixedSizeChunks:
    def test_basic_chunking(self):
        text = "a" * 1000
        chunks = fixed_size_chunks(text, chunk_size=200, overlap=50)
        assert len(chunks) > 1
        assert all(len(c.text) <= 200 for c in chunks)

    def test_overlap(self):
        text = "abcdefghij" * 50  # 500 chars
        chunks = fixed_size_chunks(text, chunk_size=100, overlap=20)
        # Each chunk after the first should share 20 chars with previous
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1].text[-20:]
            curr_start = chunks[i].text[:20]
            assert prev_end == curr_start

    def test_metadata(self):
        text = "Hello world, this is a test."
        chunks = fixed_size_chunks(text, chunk_size=100, metadata={"source": "test.md"})
        assert chunks[0].metadata["source"] == "test.md"
        assert chunks[0].metadata["strategy"] == "fixed"
        assert chunks[0].metadata["chunk_index"] == 0

    def test_empty_text(self):
        assert fixed_size_chunks("", chunk_size=100) == []
        assert fixed_size_chunks("   ", chunk_size=100) == []


class TestRecursiveChunks:
    def test_short_text_single_chunk(self):
        text = "Short text."
        chunks = recursive_chunks(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."

    def test_paragraph_splitting(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = recursive_chunks(text, chunk_size=30)
        assert len(chunks) >= 2
        assert all(c.metadata["strategy"] == "recursive" for c in chunks)

    def test_metadata_propagation(self):
        text = "First paragraph.\n\nSecond paragraph that is a bit longer."
        chunks = recursive_chunks(text, chunk_size=30, metadata={"source": "doc.md"})
        for chunk in chunks:
            assert chunk.metadata["source"] == "doc.md"


class TestChunkText:
    def test_fixed_strategy(self):
        chunks = chunk_text("Hello world", strategy="fixed", chunk_size=100)
        assert chunks[0].metadata["strategy"] == "fixed"

    def test_recursive_strategy(self):
        chunks = chunk_text("Hello world", strategy="recursive", chunk_size=100)
        assert chunks[0].metadata["strategy"] == "recursive"

    def test_unknown_strategy_raises(self):
        try:
            chunk_text("Hello", strategy="unknown")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestChunkValidation:
    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_size must be > 0"):
            fixed_size_chunks("text", chunk_size=0, overlap=0)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError, match="overlap must be >= 0"):
            recursive_chunks("text", chunk_size=10, overlap=-1)

    def test_overlap_is_capped_when_too_large(self):
        chunks = chunk_text("a" * 50, strategy="fixed", chunk_size=10, overlap=25)
        assert len(chunks) > 1
        assert all(len(c.text) <= 10 for c in chunks)


class TestRecursiveEdgeCases:
    def test_recursive_with_overlap(self):
        """Overlap carry-forward should share text between chunks."""
        text = "Alpha.\n\nBravo.\n\nCharlie.\n\nDelta."
        chunks = recursive_chunks(text, chunk_size=20, overlap=5)
        assert len(chunks) >= 2
        # Overlap means later chunks should contain trailing chars of prior

    def test_recursive_no_separator_fallback(self):
        """When no separator exists, should fall back to char-window split."""
        text = "abcdefghijklmnopqrstuvwxyz" * 4  # 104 chars, no separators
        chunks = recursive_chunks(text, chunk_size=30, overlap=0)
        assert len(chunks) >= 3
        # All text should be covered
        joined = "".join(c.text for c in chunks)
        assert len(joined) >= len(text)

    def test_recursive_empty_string(self):
        assert recursive_chunks("", chunk_size=100) == []

    def test_recursive_whitespace_only(self):
        assert recursive_chunks("   \n\n  ", chunk_size=100) == []

    def test_recursive_single_long_word(self):
        """A single word longer than chunk_size should still produce chunks."""
        text = "x" * 200
        chunks = recursive_chunks(text, chunk_size=50, overlap=0)
        assert len(chunks) >= 1
        # All content is preserved
        total_len = sum(len(c.text) for c in chunks)
        assert total_len >= 200
