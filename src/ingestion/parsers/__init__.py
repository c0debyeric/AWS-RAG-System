"""Document parsers — dispatch by file extension."""

import os

from .markdown_parser import parse_markdown
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .html_parser import parse_html
from .csv_parser import parse_csv
from .xlsx_parser import parse_xlsx
from .pptx_parser import parse_pptx


SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".pdf", ".docx",
    ".html", ".htm", ".csv",
    ".xlsx", ".xls",
    ".pptx", ".ppt",
    ".json", ".xml",
}


def parse_file(file_path: str, source: str = "") -> dict:
    """Parse a file based on its extension.

    Returns: {"text": str, "metadata": dict}
    """
    ext = os.path.splitext(file_path)[1].lower()

    if not source:
        source = os.path.basename(file_path)

    if ext == ".pdf":
        return parse_pdf(file_path, source)
    elif ext == ".docx" or ext == ".doc":
        return parse_docx(file_path, source)
    elif ext in (".md", ".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        if ext == ".md":
            return parse_markdown(text, source)
        return {"text": text, "metadata": {"source": source, "format": "text"}}
    elif ext in (".html", ".htm"):
        return parse_html(file_path, source)
    elif ext == ".csv":
        return parse_csv(file_path, source)
    elif ext in (".xlsx", ".xls"):
        return parse_xlsx(file_path, source)
    elif ext in (".pptx", ".ppt"):
        return parse_pptx(file_path, source)
    elif ext in (".json", ".xml"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return {"text": text, "metadata": {"source": source, "format": ext.lstrip(".")}}
    else:
        raise ValueError(f"Unsupported file type: {ext}")
