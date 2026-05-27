"""Bedrock Titan embedding calls.

Uses amazon.titan-embed-text-v2:0 which produces 1024-dim vectors.
Embeds one text at a time (Titan doesn't support batching natively).
"""

import json
import logging

from common.aws_clients import get_bedrock_runtime
from common.config import get_config

logger = logging.getLogger(__name__)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using Bedrock Titan.

    Returns list of embedding vectors (1024-dim each).
    """
    config = get_config()
    client = get_bedrock_runtime()
    embeddings = []

    for i, text in enumerate(texts):
        response = client.invoke_model(
            modelId=config.embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": text,
                "dimensions": config.embedding_dim,
            }),
        )

        result = json.loads(response["body"].read())
        embeddings.append(result["embedding"])

    logger.info(f"Embedded {len(texts)} chunks ({config.embedding_dim}-dim)")
    return embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
