"""Tests for document parsers."""

import os
import tempfile
from ingestion.parsers import parse_file
from ingestion.parsers.markdown_parser import parse_markdown


SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_docs")


class TestMarkdownParser:
    def test_extracts_title(self):
        text = "# My Document\n\nSome content here."
        result = parse_markdown(text, source="test.md")
        assert result["metadata"]["title"] == "My Document"
        assert result["metadata"]["format"] == "markdown"

    def test_no_title(self):
        text = "Just some text without a heading."
        result = parse_markdown(text, source="test.md")
        assert result["metadata"]["title"] == ""

    def test_preserves_full_text(self):
        text = "# Title\n\nParagraph 1\n\nParagraph 2"
        result = parse_markdown(text, source="test.md")
        assert result["text"] == text

    def test_source_in_metadata(self):
        result = parse_markdown("content", source="docs/readme.md")
        assert result["metadata"]["source"] == "docs/readme.md"


class TestParseFile:
    def test_parse_markdown_file(self):
        sample = os.path.join(SAMPLE_DOCS_DIR, "server-restart-procedure.md")
        if not os.path.exists(sample):
            return  # skip if sample docs not available
        result = parse_file(sample)
        assert len(result["text"]) > 100
        assert result["metadata"]["format"] == "markdown"
        assert result["metadata"]["title"] == "Server Restart Procedure"

    def test_parse_txt_file(self):
        f = tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8")
        f.write("Plain text content for testing.")
        f.close()
        try:
            result = parse_file(f.name, source="test.txt")
            assert result["text"] == "Plain text content for testing."
            assert result["metadata"]["format"] == "text"
        finally:
            os.unlink(f.name)

    def test_unsupported_extension_raises(self):
        f = tempfile.NamedTemporaryFile(suffix=".xyz", delete=False)
        fname = f.name
        f.close()
        try:
            try:
                parse_file(fname)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Unsupported" in str(e)
        finally:
            os.unlink(fname)
