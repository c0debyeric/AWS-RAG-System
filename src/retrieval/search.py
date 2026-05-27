"""Vector search over pgvector."""

import json
import logging

from common.db import get_connection
from common.config import get_config
from ingestion.embedder import embed_query

logger = logging.getLogger(__name__)


def vector_search(query: str, top_k: int | None = None) -> list[dict]:
    """Search pgvector for the most similar chunks to a query.

    Returns list of dicts:
        {"content": str, "metadata": dict, "similarity": float, "source_doc": str}
    """
    config = get_config()
    if top_k is None:
        top_k = config.top_k

    query_embedding = embed_query(query)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, metadata, source_doc,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (json.dumps(query_embedding), json.dumps(query_embedding), top_k),
        )
        rows = cur.fetchall()

    results = []
    for row in rows:
        meta = row[1]
        if isinstance(meta, str):
            meta = json.loads(meta)
        results.append({
            "content": row[0],
            "metadata": meta,
            "source_doc": row[2],
            "similarity": float(row[3]),
        })

    logger.info(f"Search returned {len(results)} results for: {query[:60]}")
    return results
