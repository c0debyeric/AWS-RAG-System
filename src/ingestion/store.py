"""pgvector storage operations."""

import json
import logging

import numpy as np

from common.db import get_connection

logger = logging.getLogger(__name__)


def store_chunks(chunks: list[dict], embeddings: list[list[float]]) -> int:
    """Store chunks with embeddings in pgvector.

    Args:
        chunks: list of {"text": str, "metadata": dict, "token_count": int}
        embeddings: list of embedding vectors

    Returns:
        Number of chunks stored.
    """
    conn = get_connection()

    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO documents (content, embedding, metadata, source_doc, token_count)
                VALUES (%s, %s::vector, %s, %s, %s)
                """,
                (
                    chunk["text"],
                    json.dumps(embedding),
                    json.dumps(chunk["metadata"]),
                    chunk["metadata"].get("source", "unknown"),
                    chunk["token_count"],
                ),
            )

    logger.info(f"Stored {len(chunks)} chunks in pgvector")
    return len(chunks)


def get_document_count() -> int:
    """Get total number of chunks in the store."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM documents")
        return cur.fetchone()[0]


def delete_by_source(source_doc: str) -> int:
    """Delete all chunks for a given source document (for re-ingestion)."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE source_doc = %s", (source_doc,))
        count = cur.rowcount
    logger.info(f"Deleted {count} chunks for source: {source_doc}")
    return count
