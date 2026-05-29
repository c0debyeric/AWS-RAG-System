"""
Teams RAG Chatbot - Bot Handler

Lambda function that receives messages from Azure Bot Service (via API Gateway)
and responds using the Bot Framework reply API (POST back to serviceUrl).
"""
import json
import logging
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

# Ensure src modules are importable in Lambda flat-zip layout
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    sys.path.insert(0, os.environ.get("LAMBDA_TASK_ROOT", "/var/task"))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from retrieval.search import vector_search
from retrieval.generator import generate_answer
from conversation_logging.logger import log_query

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Bot credentials from Secrets Manager
_bot_credentials = None


def _get_bot_credentials():
    """Load bot credentials from Secrets Manager (cached)."""
    global _bot_credentials
    if _bot_credentials is None:
        secret_arn = os.environ.get("BOT_SECRET_ARN", "")
        if not secret_arn:
            logger.error("BOT_SECRET_ARN not set")
            return {}
        sm = boto3.client("secretsmanager")
        resp = sm.get_secret_value(SecretId=secret_arn)
        _bot_credentials = json.loads(resp["SecretString"])
    return _bot_credentials


def _get_bot_token(creds: dict) -> str:
    """Get an access token from Microsoft to reply to the conversation."""
    app_id = creds.get("MicrosoftAppId", "")
    app_password = creds.get("MicrosoftAppPassword", "")
    tenant_id = creds.get("MicrosoftAppTenantId", "")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": app_id,
        "client_secret": app_password,
        "scope": "https://api.botframework.com/.default",
    }).encode()

    req = urllib.request.Request(token_url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=10) as resp:
        token_data = json.loads(resp.read())
    return token_data["access_token"]


def _send_reply(service_url: str, conversation_id: str, activity_id: str, text: str, token: str):
    """POST a reply activity back to Bot Framework via serviceUrl."""
    reply_url = f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities/{activity_id}"
    reply_activity = {
        "type": "message",
        "text": text,
    }
    payload = json.dumps(reply_activity).encode()

    req = urllib.request.Request(reply_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            logger.info(f"Reply sent, status: {resp.status}")
    except urllib.error.HTTPError as e:
        logger.error(f"Reply failed: {e.code} {e.read().decode()}")
        raise


def handler(event, context):
    """Lambda handler for Bot Framework messages via API Gateway."""
    body = json.loads(event.get("body", "{}"))
    activity_type = body.get("type")

    if activity_type == "message":
        user_text = body.get("text", "").strip()
        user_id = body.get("from", {}).get("id", "")
        service_url = body.get("serviceUrl", "")
        conversation_id = body.get("conversation", {}).get("id", "")
        activity_id = body.get("id", "")

        if not user_text:
            return _build_response(200, {})

        # Generate the answer
        answer_text = _handle_query(user_text, user_id)

        # Reply via Bot Framework API
        try:
            creds = _get_bot_credentials()
            token = _get_bot_token(creds)
            _send_reply(service_url, conversation_id, activity_id, answer_text, token)
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

        return _build_response(200, {})

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
