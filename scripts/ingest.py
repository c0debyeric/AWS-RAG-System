"""CLI: Batch ingest documents into pgvector.

Usage:
    python scripts/ingest.py --source data/sample_docs
    python scripts/ingest.py --source s3 --bucket my-docs-bucket --prefix sharepoint/
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.config import get_config
from ingestion.loader import ingest_directory, ingest_from_s3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into RAG knowledge base")
    parser.add_argument("--source", required=True, help="Local directory path or 's3' for S3 bucket")
    parser.add_argument("--bucket", help="S3 bucket name (required if source=s3)")
    parser.add_argument("--prefix", default="", help="S3 key prefix")
    parser.add_argument("--no-replace", action="store_true", help="Don't replace existing chunks")

    args = parser.parse_args()

    if args.source == "s3":
        if not args.bucket:
            config = get_config()
            args.bucket = config.documents_bucket
        if not args.bucket:
            parser.error("--bucket required when source=s3")

        print(f"Ingesting from s3://{args.bucket}/{args.prefix}")
        stats = ingest_from_s3(args.bucket, args.prefix, replace=not args.no_replace)
    else:
        if not os.path.isdir(args.source):
            parser.error(f"Directory not found: {args.source}")

        print(f"Ingesting from {args.source}")
        stats = ingest_directory(args.source, replace=not args.no_replace)

    print(f"\nIngestion complete:")
    print(f"  Documents ingested: {stats['ingested']}")
    print(f"  Chunks created:     {stats['chunks']}")
    print(f"  Skipped:            {stats['skipped']}")
    if stats["errors"]:
        print(f"  Errors:             {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"    - {err['file']}: {err['error']}")


if __name__ == "__main__":
    main()
