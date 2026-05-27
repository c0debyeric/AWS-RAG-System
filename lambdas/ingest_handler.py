"""Lambda handler for document ingestion triggered by S3 events.

When a file is uploaded to the documents S3 bucket, this Lambda:
1. Downloads the file
2. Parses it (PDF, DOCX, MD, TXT)
3. Chunks the text with overlap
4. Embeds each chunk via Bedrock Titan
5. Stores chunks + embeddings in pgvector
"""
import json
import logging
import os
import sys
import tempfile
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.aws_clients import get_s3
from common.config import get_config
from ingestion.parsers import parse_file, SUPPORTED_EXTENSIONS
from ingestion.chunker import RecursiveTextChunker
from ingestion.embedder import embed_texts
from ingestion.store import store_chunks, delete_by_source

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Process S3 event — ingest new/updated documents."""
    config = get_config()
    chunker = RecursiveTextChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    s3 = get_s3()

    results = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        ext = os.path.splitext(key)[1].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            logger.info(f"Skipping unsupported file: {key}")
            results.append({"key": key, "status": "skipped"})
            continue

        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
                s3.download_file(bucket, key, tmp.name)

                parsed = parse_file(tmp.name, source=key)
                if not parsed["text"].strip():
                    results.append({"key": key, "status": "empty"})
                    continue

                # Delete existing chunks for this source (re-ingestion safe)
                delete_by_source(key)

                chunks = chunker.chunk(parsed["text"], metadata=parsed["metadata"])
                texts = [c["text"] for c in chunks]
                embeddings = embed_texts(texts)
                store_chunks(chunks, embeddings)

                results.append({"key": key, "status": "ingested", "chunks": len(chunks)})
                logger.info(f"Ingested {key}: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to ingest {key}: {e}")
            results.append({"key": key, "status": "error", "error": str(e)})

    return {
        "statusCode": 200,
        "body": json.dumps({"results": results}),
    }
