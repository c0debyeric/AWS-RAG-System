"""Document parsers — dispatch by file extension."""

import os

from .markdown_parser import parse_markdown
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def parse_file(file_path: str, source: str = "") -> dict:
    """Parse a file based on its extension.

    Returns: {"text": str, "metadata": dict}
    """
    ext = os.path.splitext(file_path)[1].lower()

    if not source:
        source = os.path.basename(file_path)

    if ext == ".pdf":
        return parse_pdf(file_path, source)
    elif ext == ".docx":
        return parse_docx(file_path, source)
    elif ext in (".md", ".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        if ext == ".md":
            return parse_markdown(text, source)
        return {"text": text, "metadata": {"source": source, "format": "text"}}
    else:
        raise ValueError(f"Unsupported file type: {ext}")
