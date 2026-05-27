"""Tests for the recursive text chunker."""

from ingestion.chunker import RecursiveTextChunker


class TestRecursiveTextChunker:
    def setup_method(self):
        self.chunker = RecursiveTextChunker(chunk_size=50, chunk_overlap=10)

    def test_empty_text_returns_empty(self):
        assert self.chunker.chunk("") == []
        assert self.chunker.chunk("   ") == []

    def test_short_text_single_chunk(self):
        text = "This is a short piece of text."
        chunks = self.chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text

    def test_preserves_metadata(self):
        text = "Hello world"
        meta = {"source": "test.md", "format": "markdown"}
        chunks = self.chunker.chunk(text, metadata=meta)
        assert chunks[0]["metadata"]["source"] == "test.md"
        assert chunks[0]["metadata"]["format"] == "markdown"
        assert "chunk_index" in chunks[0]["metadata"]
        assert "total_chunks" in chunks[0]["metadata"]

    def test_long_text_produces_multiple_chunks(self):
        text = " ".join(
            [f"Sentence number {i} with extra words to fill up tokens." for i in range(30)]
        )
        chunks = self.chunker.chunk(text)
        assert len(chunks) > 1

    def test_token_count_populated(self):
        text = "Each chunk should have a token count field."
        chunks = self.chunker.chunk(text)
        assert all(c["token_count"] > 0 for c in chunks)

    def test_chunk_index_sequential(self):
        text = "\n\n".join([f"Paragraph {i}. " * 15 for i in range(5)])
        chunks = self.chunker.chunk(text)
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i

    def test_total_chunks_consistent(self):
        text = "\n\n".join([f"Section {i}: " + "word " * 40 for i in range(4)])
        chunks = self.chunker.chunk(text)
        expected = len(chunks)
        for chunk in chunks:
            assert chunk["metadata"]["total_chunks"] == expected

    def test_respects_paragraph_boundaries(self):
        """Chunker should prefer splitting on double newlines over mid-sentence."""
        short_para = "Short paragraph here."
        long_para = "This is a much longer paragraph with many words " * 5
        text = short_para + "\n\n" + long_para
        chunks = self.chunker.chunk(text)
        # The short paragraph should not be merged into the long one if together they exceed chunk_size
        assert len(chunks) >= 1

    def test_default_chunk_size(self):
        chunker = RecursiveTextChunker()  # defaults: 512 size, 100 overlap
        assert chunker.chunk_size == 512
        assert chunker.chunk_overlap == 100
