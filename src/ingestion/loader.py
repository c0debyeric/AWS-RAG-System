"""Document loader — reads from local directory or S3, orchestrates ingestion."""

import logging
import os
import tempfile

from common.aws_clients import get_s3
from common.config import get_config
from ingestion.parsers import parse_file, SUPPORTED_EXTENSIONS
from ingestion.chunker import RecursiveTextChunker
from ingestion.embedder import embed_texts
from ingestion.store import store_chunks, delete_by_source

logger = logging.getLogger(__name__)


def ingest_directory(directory: str, replace: bool = True) -> dict:
    """Ingest all supported documents from a local directory.

    Args:
        directory: Path to directory containing documents.
        replace: If True, delete existing chunks for each doc before re-ingesting.

    Returns: {"ingested": int, "chunks": int, "skipped": int, "errors": list}
    """
    config = get_config()
    chunker = RecursiveTextChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    stats = {"ingested": 0, "chunks": 0, "skipped": 0, "errors": []}

    for filename in sorted(os.listdir(directory)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            stats["skipped"] += 1
            continue

        file_path = os.path.join(directory, filename)
        try:
            n = _ingest_file(file_path, filename, chunker, replace)
            stats["ingested"] += 1
            stats["chunks"] += n
        except Exception as e:
            logger.error(f"Failed to ingest {filename}: {e}")
            stats["errors"].append({"file": filename, "error": str(e)})

    return stats


def ingest_from_s3(bucket: str, prefix: str = "", replace: bool = True) -> dict:
    """Ingest documents from an S3 bucket.

    Args:
        bucket: S3 bucket name.
        prefix: S3 key prefix to filter objects.
        replace: If True, delete existing chunks before re-ingesting.

    Returns: {"ingested": int, "chunks": int, "skipped": int, "errors": list}
    """
    config = get_config()
    s3 = get_s3()
    chunker = RecursiveTextChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    stats = {"ingested": 0, "chunks": 0, "skipped": 0, "errors": []}

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            ext = os.path.splitext(key)[1].lower()

            if ext not in SUPPORTED_EXTENSIONS:
                stats["skipped"] += 1
                continue

            try:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
                    s3.download_file(bucket, key, tmp.name)
                    n = _ingest_file(tmp.name, key, chunker, replace)
                    stats["ingested"] += 1
                    stats["chunks"] += n
            except Exception as e:
                logger.error(f"Failed to ingest s3://{bucket}/{key}: {e}")
                stats["errors"].append({"file": key, "error": str(e)})

    return stats


def _ingest_file(file_path: str, source: str, chunker: RecursiveTextChunker, replace: bool) -> int:
    """Parse, chunk, embed, and store a single file. Returns chunk count."""
    parsed = parse_file(file_path, source=source)

    if not parsed["text"].strip():
        logger.warning(f"Empty document: {source}")
        return 0

    if replace:
        delete_by_source(source)

    chunks = chunker.chunk(parsed["text"], metadata=parsed["metadata"])

    if not chunks:
        logger.warning(f"No chunks produced for: {source}")
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    stored = store_chunks(chunks, embeddings)
    logger.info(f"Ingested {source}: {stored} chunks")
    return stored
