"""CSV document parser."""

import csv
import logging

logger = logging.getLogger(__name__)


def parse_csv(file_path: str, source: str = "") -> dict:
    """Convert a CSV file to a readable text representation.

    Each row is rendered as a line with column headers as labels.
    Returns: {"text": str, "metadata": dict}
    """
    rows = []

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        for row in reader:
            parts = [f"{k}: {v}" for k, v in row.items() if v and v.strip()]
            if parts:
                rows.append(" | ".join(parts))

    full_text = "\n".join(rows)

    return {
        "text": full_text,
        "metadata": {
            "source": source,
            "format": "csv",
            "row_count": len(rows),
            "columns": headers,
        },
    }
