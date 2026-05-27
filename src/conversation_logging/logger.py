"""Conversation logging — structured CloudWatch logs.

Every RAG query gets logged as a structured JSON entry.
CloudWatch Logs Insights can query these fields directly:

    fields @timestamp, query, latency_ms, retrieved_chunk_count
    | filter event_type = "rag_query"
    | sort latency_ms desc
    | limit 50
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("rag.conversation")


def log_query(
    query: str,
    retrieved_chunks: list[dict],
    answer: str,
    sources: list[str],
    latency_ms: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
    user_id: str = "",
):
    """Log a complete RAG query cycle as a structured CloudWatch log entry."""
    log_entry = {
        "event_type": "rag_query",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "retrieved_chunk_count": len(retrieved_chunks),
        "retrieved_chunks": [
            {
                "source": c.get("source_doc", ""),
                "similarity": round(c.get("similarity", 0), 4),
                "content_preview": c.get("content", "")[:200],
            }
            for c in retrieved_chunks
        ],
        "answer_length": len(answer),
        "sources": sources,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "user_id": user_id,
    }

    logger.info(json.dumps(log_entry))
