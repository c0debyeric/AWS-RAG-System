"""
Teams RAG Chatbot - Bot Handler

Lambda function that receives messages from Azure Bot Service (via API Gateway)
and responds using the custom RAG pipeline (pgvector search + Bedrock Claude).
"""
import json
import logging
import os
import sys

# Ensure src modules are importable in Lambda flat-zip layout
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    sys.path.insert(0, os.environ.get("LAMBDA_TASK_ROOT", "/var/task"))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
            return _build_response(200, {"type": "message", "text": "Please send a message with your question."})

        answer_text = _handle_query(user_text, user_id)
        return _build_response(200, {"type": "message", "text": answer_text})

    if activity_type == "conversationUpdate":
        return _build_response(200, {})

    return _build_response(200, {})


def _handle_query(query: str, user_id: str = "") -> str:
    """Run the full RAG pipeline: search → generate → log."""
    try:
        chunks = vector_search(query)

        if not chunks:
            return "I couldn't find relevant information in the knowledge base for that question."

        result = generate_answer(query, chunks)
        answer = result["answer"]

        if result["sources"]:
            answer += "\n\n**Sources:**\n" + "\n".join(f"- {s}" for s in result["sources"])

        log_query(
            query=query,
            retrieved_chunks=chunks,
            answer=result["answer"],
            sources=result["sources"],
            latency_ms=result["latency_ms"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            user_id=user_id,
        )

        return answer

    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        return "Sorry, I encountered an error processing your question. Please try again."


def _build_response(status_code: int, body: dict) -> dict:
    """Build API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
