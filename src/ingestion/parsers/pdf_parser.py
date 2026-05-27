"""PDF document parser using pdfplumber."""

import logging

import pdfplumber

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str, source: str = "") -> dict:
    """Extract text from a PDF file.

    Returns: {"text": str, "metadata": dict}
    """
    pages = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)

    full_text = "\n\n".join(pages)

    return {
        "text": full_text,
        "metadata": {
            "source": source,
            "format": "pdf",
            "page_count": len(pages),
        },
    }
