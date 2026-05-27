"""Recursive text splitter for document chunking.

Splits on natural boundaries (paragraphs → sentences → words) with
token-aware sizing. Uses cl100k_base encoding (same tokenizer family
as Claude / Titan).
"""

import tiktoken


class RecursiveTextChunker:
    """Split text recursively by natural boundaries with token-aware sizing."""

    SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def token_count(self, text: str) -> int:
        return len(self._encoder.encode(text))

    def chunk(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Split text into chunks with metadata.

        Returns list of dicts: {"text": str, "metadata": dict, "token_count": int}
        """
        if not text.strip():
            return []

        raw_chunks = self._split(text, self.SEPARATORS)
        merged = self._merge_with_overlap(raw_chunks)

        result = []
        for i, chunk_text in enumerate(merged):
            chunk_meta = dict(metadata) if metadata else {}
            chunk_meta["chunk_index"] = i
            chunk_meta["total_chunks"] = len(merged)
            result.append({
                "text": chunk_text,
                "metadata": chunk_meta,
                "token_count": self.token_count(chunk_text),
            })

        return result

    def _split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using progressively finer separators."""
        if not separators:
            return [text]

        sep = separators[0]
        remaining_seps = separators[1:]

        if not sep:
            # Character-level split as last resort
            chunks = []
            current = ""
            for char in text:
                current += char
                if self.token_count(current) >= self.chunk_size:
                    chunks.append(current)
                    current = ""
            if current:
                chunks.append(current)
            return chunks

        parts = text.split(sep)
        result = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part

            if self.token_count(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    result.append(current)

                if self.token_count(part) > self.chunk_size:
                    sub_chunks = self._split(part, remaining_seps)
                    result.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current:
            result.append(current)

        return result

    def _merge_with_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between consecutive chunks."""
        if len(chunks) <= 1:
            return chunks

        result = [chunks[0]]

        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            curr = chunks[i]

            overlap_text = self._get_tail_tokens(prev, self.chunk_overlap)

            if overlap_text:
                merged = overlap_text + " " + curr
                if self.token_count(merged) > self.chunk_size:
                    merged = self._trim_to_tokens(merged, self.chunk_size)
                result.append(merged)
            else:
                result.append(curr)

        return result

    def _get_tail_tokens(self, text: str, n_tokens: int) -> str:
        """Get the last n_tokens from text."""
        tokens = self._encoder.encode(text)
        if len(tokens) <= n_tokens:
            return text
        return self._encoder.decode(tokens[-n_tokens:])

    def _trim_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trim text to max_tokens."""
        tokens = self._encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self._encoder.decode(tokens[:max_tokens])
