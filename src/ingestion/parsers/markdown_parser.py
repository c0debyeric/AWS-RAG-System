"""Markdown document parser."""


def parse_markdown(text: str, source: str = "") -> dict:
    """Parse a markdown document.

    Returns: {"text": str, "metadata": dict}
    """
    title = ""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    return {
        "text": text,
        "metadata": {
            "source": source,
            "title": title,
            "format": "markdown",
        },
    }
