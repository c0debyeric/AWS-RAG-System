"""
Teams RAG Chatbot - Bot Handler

This Lambda function receives messages from Azure Bot Service (via API Gateway)
and responds using Amazon Bedrock Knowledge Bases for RAG.
"""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent = boto3.client("bedrock-agent-runtime")

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
FOUNDATION_MODEL_ID = os.environ["FOUNDATION_MODEL_ID"]


def handler(event, context):
    """Lambda handler for Bot Framework messages via API Gateway."""
    body = json.loads(event.get("body", "{}"))

    # Bot Framework activity type
    activity_type = body.get("type")

    if activity_type == "message":
        user_text = body.get("text", "").strip()
        if not user_text:
            return _build_response(200, {"type": "message", "text": "Please send a message with your question."})

        # Call Bedrock KB RetrieveAndGenerate
        answer = retrieve_and_generate(user_text)
        return _build_response(200, {"type": "message", "text": answer})

    # Respond to conversationUpdate (bot added to conversation)
    if activity_type == "conversationUpdate":
        return _build_response(200, {})

    return _build_response(200, {})


def retrieve_and_generate(query: str) -> str:
    """Call Bedrock Knowledge Base RetrieveAndGenerate API."""
    try:
        response = bedrock_agent.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": f"arn:aws:bedrock:us-east-1::foundation-model/{FOUNDATION_MODEL_ID}",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "numberOfResults": 5,
                        }
                    },
                },
            },
        )

        output_text = response.get("output", {}).get("text", "I couldn't find an answer to that question.")

        # Append source citations if available
        citations = response.get("citations", [])
        if citations:
            sources = set()
            for citation in citations:
                for ref in citation.get("retrievedReferences", []):
                    location = ref.get("location", {})
                    if location.get("type") == "SHAREPOINT":
                        url = location.get("sharePointLocation", {}).get("url", "")
                        if url:
                            sources.add(url)
            if sources:
                output_text += "\n\n**Sources:**\n" + "\n".join(f"- {s}" for s in sources)

        return output_text

    except Exception as e:
        logger.error(f"Bedrock KB error: {e}")
        return "Sorry, I encountered an error processing your question. Please try again."


def _build_response(status_code: int, body: dict) -> dict:
    """Build API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
