"""DOCX document parser using python-docx."""

import logging

from docx import Document

logger = logging.getLogger(__name__)


def parse_docx(file_path: str, source: str = "") -> dict:
    """Extract text from a DOCX file, preserving heading structure as markdown.

    Returns: {"text": str, "metadata": dict}
    """
    doc = Document(file_path)

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        # Convert Word headings to markdown headings
        if para.style and para.style.name.startswith("Heading"):
            level_str = para.style.name.replace("Heading ", "").replace("Heading", "1")
            try:
                level = int(level_str)
            except ValueError:
                level = 1
            text = "#" * level + " " + text
        paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)

    return {
        "text": full_text,
        "metadata": {
            "source": source,
            "format": "docx",
            "paragraph_count": len(paragraphs),
        },
    }
