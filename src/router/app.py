"""
Teams Bot Router — Lambda Handler

Receives Bot Framework activities from API Gateway, routes to the correct
backend Lambda (RAG or Account Vending) based on Adaptive Card selection,
and replies via the Bot Framework serviceUrl.

Add a new route on your existing API Gateway pointing to this Lambda.
Set the Azure Bot messaging endpoint to that API Gateway URL.
"""

import json
import logging
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    sys.path.insert(0, os.environ.get("LAMBDA_TASK_ROOT", "/var/task"))

import boto3

from cards import build_mode_selector_card
from sessions import AgentMode, SessionStore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Initialised once per Lambda container ────────────────────────────
_bot_credentials = None
_lambda_client = boto3.client("lambda")
_sessions = SessionStore()

RAG_LAMBDA_ARN = os.environ.get("RAG_LAMBDA_ARN", "")
VENDING_LAMBDA_ARN = os.environ.get("VENDING_LAMBDA_ARN", "")


# ── Bot Framework helpers (same pattern as RAG project) ──────────────

def _get_bot_credentials() -> dict:
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
    """POST a text reply back to Bot Framework via serviceUrl."""
    reply_url = f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities/{activity_id}"
    reply_activity = {"type": "message", "text": text}
    payload = json.dumps(reply_activity).encode()

    req = urllib.request.Request(reply_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        logger.info("Reply sent, status: %s", resp.status)


def _send_card_reply(service_url: str, conversation_id: str, activity_id: str, card: dict, token: str):
    """POST an Adaptive Card reply back to Bot Framework via serviceUrl."""
    reply_url = f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities/{activity_id}"
    reply_activity = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }
    payload = json.dumps(reply_activity).encode()

    req = urllib.request.Request(reply_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        logger.info("Card reply sent, status: %s", resp.status)


# ── Backend dispatch ─────────────────────────────────────────────────

def _invoke_rag(conversation_id: str, user_text: str) -> str:
    resp = _lambda_client.invoke(
        FunctionName=RAG_LAMBDA_ARN,
        InvocationType="RequestResponse",
        Payload=json.dumps({"direct_query": True, "query": user_text, "user_id": conversation_id}),
    )
    result = json.loads(resp["Payload"].read())
    return result.get("answer", "No answer returned from the knowledge base.")


def _invoke_vending(conversation_id: str, user_text: str) -> str:
    resp = _lambda_client.invoke(
        FunctionName=VENDING_LAMBDA_ARN,
        InvocationType="RequestResponse",
        Payload=json.dumps({"conversation_id": conversation_id, "user_text": user_text}),
    )
    result = json.loads(resp["Payload"].read())
    return result.get("response", "No response from account vending agent.")


# ── Lambda entry point ───────────────────────────────────────────────

def handler(event, context):
    """Lambda handler — receives Bot Framework activities via API Gateway."""
    body = json.loads(event.get("body", "{}"))
    activity_type = body.get("type")

    if activity_type == "conversationUpdate":
        # New member added → send welcome card
        members_added = body.get("membersAdded", [])
        recipient_id = body.get("recipient", {}).get("id", "")
        if any(m.get("id") != recipient_id for m in members_added):
            _reply_with_card(body)
        return _build_response(200)

    if activity_type != "message":
        return _build_response(200)

    conversation_id = body.get("conversation", {}).get("id", "")
    value = body.get("value")  # Adaptive Card submit payload
    user_text = (body.get("text") or "").strip()

    try:
        creds = _get_bot_credentials()
        token = _get_bot_token(creds)
        service_url = body.get("serviceUrl", "")
        activity_id = body.get("id", "")

        # 1. Adaptive Card selection
        if value and value.get("action") == "select_agent":
            agent = AgentMode(value["agent"])
            _sessions.create(conversation_id, agent)
            label = "Knowledge Base" if agent == AgentMode.RAG else "AWS Account Setup"
            _send_reply(service_url, conversation_id, activity_id, f"Switched to **{label}** mode. How can I help?", token)
            return _build_response(200)

        # 2. Menu / switch commands
        if user_text.lower() in ("menu", "switch", "back", "home"):
            _sessions.delete(conversation_id)
            _send_card_reply(service_url, conversation_id, activity_id, build_mode_selector_card(), token)
            return _build_response(200)

        # 3. No active session → show mode selector card
        active_agent = _sessions.get(conversation_id)
        if active_agent is None:
            _send_card_reply(service_url, conversation_id, activity_id, build_mode_selector_card(), token)
            return _build_response(200)

        # 4. Route to the active backend
        if active_agent == AgentMode.RAG:
            response_text = _invoke_rag(conversation_id, user_text)
        else:
            response_text = _invoke_vending(conversation_id, user_text)

        _send_reply(service_url, conversation_id, activity_id, response_text, token)

    except Exception:
        logger.exception("Error processing message")

    return _build_response(200)


def _reply_with_card(body: dict):
    """Send the mode selector card for conversationUpdate events."""
    try:
        creds = _get_bot_credentials()
        token = _get_bot_token(creds)
        service_url = body.get("serviceUrl", "")
        conversation_id = body.get("conversation", {}).get("id", "")
        activity_id = body.get("id", "")
        _send_card_reply(service_url, conversation_id, activity_id, build_mode_selector_card(), token)
    except Exception:
        logger.exception("Failed to send welcome card")


def _build_response(status_code: int) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({}),
    }
