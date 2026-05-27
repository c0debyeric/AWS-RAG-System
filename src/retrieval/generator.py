"""Bedrock generation with RAG context (model-agnostic via Converse API)."""

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
    """Generate an answer using Bedrock Converse API (works with any model).

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

    response = client.converse(
        modelId=config.generation_model_id,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {"role": "user", "content": [{"text": user_message}]},
        ],
        inferenceConfig={
            "maxTokens": 1024,
            "temperature": 0.0,
        },
    )

    latency_ms = (time.time() - start) * 1000

    answer = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})

    return {
        "answer": answer,
        "sources": sources,
        "latency_ms": round(latency_ms, 1),
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
    }
