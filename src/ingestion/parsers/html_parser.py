"""HTML document parser using BeautifulSoup."""

import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_html(file_path: str, source: str = "") -> dict:
    """Extract text from an HTML file, stripping tags.

    Returns: {"text": str, "metadata": dict}
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = soup.get_text(separator="\n", strip=True)

    return {
        "text": text,
        "metadata": {
            "source": source,
            "title": title,
            "format": "html",
        },
    }
