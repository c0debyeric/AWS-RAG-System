"""Bedrock Claude generation with RAG context."""

import json
import logging
import time

from common.aws_clients import get_bedrock_runtime
from common.config import get_config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an assistant for engineering teams.
Answer questions using ONLY the provided context documents.
If the context doesn't contain the answer, say "I don't have information about that in the current documentation."
Always cite the source document name for each claim.
Never make up information not present in the context."""


def generate_answer(query: str, retrieved_chunks: list[dict]) -> dict:
    """Generate an answer using Claude with RAG context.

    Args:
        query: User's question.
        retrieved_chunks: List of {"content": str, "metadata": dict, "source_doc": str, "similarity": float}.

    Returns:
        {"answer": str, "sources": list[str], "latency_ms": float,
         "input_tokens": int, "output_tokens": int}
    """
    config = get_config()
    client = get_bedrock_runtime()

    # Build context from retrieved chunks
    context_parts = []
    sources = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source = chunk.get("source_doc", "unknown")
        if source not in sources:
            sources.append(source)
        context_parts.append(f"[Document {i}: {source}]\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)

    user_message = f"""Context documents:

{context}

---

Question: {query}"""

    start = time.time()

    response = client.invoke_model(
        modelId=config.generation_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "temperature": 0.0,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": user_message},
            ],
        }),
    )

    latency_ms = (time.time() - start) * 1000
    result = json.loads(response["body"].read())

    answer = result["content"][0]["text"]
    usage = result.get("usage", {})

    return {
        "answer": answer,
        "sources": sources,
        "latency_ms": round(latency_ms, 1),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }
