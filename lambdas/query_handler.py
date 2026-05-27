"""Lambda handler for RAG queries via API Gateway.

Alternative entry point to src/bot/app.py — same pipeline,
different packaging strategy (bundles src/ as a layer).
"""
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from retrieval.search import vector_search
from retrieval.generator import generate_answer
from conversation_logging.logger import log_query

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler for Bot Framework messages via API Gateway."""
    body = json.loads(event.get("body", "{}"))
    activity_type = body.get("type")

    if activity_type == "message":
        user_text = body.get("text", "").strip()
        user_id = body.get("from", {}).get("id", "")

        if not user_text:
            return _response(200, {"type": "message", "text": "Please send a message with your question."})

        try:
            chunks = vector_search(user_text)

            if not chunks:
                answer_text = "I couldn't find relevant information in the knowledge base for that question."
            else:
                result = generate_answer(user_text, chunks)
                answer_text = result["answer"]

                if result["sources"]:
                    answer_text += "\n\n**Sources:**\n" + "\n".join(f"- {s}" for s in result["sources"])

                log_query(
                    query=user_text,
                    retrieved_chunks=chunks,
                    answer=result["answer"],
                    sources=result["sources"],
                    latency_ms=result["latency_ms"],
                    input_tokens=result["input_tokens"],
                    output_tokens=result["output_tokens"],
                    user_id=user_id,
                )

        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            answer_text = "Sorry, I encountered an error processing your question. Please try again."

        return _response(200, {"type": "message", "text": answer_text})

    if activity_type == "conversationUpdate":
        return _response(200, {})

    return _response(200, {})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
