"""
Set up pgvector database schema for the custom RAG pipeline.

Creates the documents table with HNSW vector index for cosine similarity search.

Usage (local dev):
    python setup_pgvector.py

Usage (Aurora):
    python setup_pgvector.py --host <aurora-endpoint> --password <db-password>
"""
import argparse
import os
import psycopg2


def setup_pgvector(host: str, port: int, dbname: str, user: str, password: str):
    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("Creating pgvector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    print("Creating documents table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            embedding vector(1024),
            metadata JSONB DEFAULT '{}',
            source_doc TEXT NOT NULL,
            token_count INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    print("Creating HNSW vector index (cosine similarity)...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_embedding
        ON documents USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200);
    """)

    print("Creating source_doc index (for re-ingestion deletes)...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_source
        ON documents (source_doc);
    """)

    print("Creating metadata GIN index (for filtered search)...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_metadata
        ON documents USING gin (metadata);
    """)

    cur.execute("SELECT COUNT(*) FROM documents;")
    count = cur.fetchone()[0]
    print(f"\nSetup complete. Documents table has {count} rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up pgvector database for RAG pipeline")
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DB_PORT", "5432")))
    parser.add_argument("--dbname", default=os.environ.get("DB_NAME", "ragdb"))
    parser.add_argument("--user", default=os.environ.get("DB_USER", "postgres"))
    parser.add_argument("--password", default=os.environ.get("DB_PASSWORD", "localdev"))
    args = parser.parse_args()

    setup_pgvector(args.host, args.port, args.dbname, args.user, args.password)
