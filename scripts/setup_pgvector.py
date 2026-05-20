"""
One-time setup script for Aurora PostgreSQL pgvector.
Run this AFTER terraform apply creates the Aurora cluster.

This creates the pgvector extension and the schema/table
that Bedrock Knowledge Base expects.

Usage:
    python setup_pgvector.py --host <aurora-endpoint> --password <db-password>
"""
import argparse
import psycopg2


def setup_pgvector(host: str, port: int, dbname: str, user: str, password: str):
    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("Creating pgvector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    print("Creating schema...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS bedrock_integration;")

    print("Creating knowledge base table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bedrock_integration.bedrock_kb (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            embedding vector(1024),
            chunks TEXT,
            metadata JSONB
        );
    """)

    print("Creating vector index...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS bedrock_kb_embedding_idx
        ON bedrock_integration.bedrock_kb
        USING hnsw (embedding vector_cosine_ops);
    """)

    print("Creating text search index...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS bedrock_kb_chunks_idx
        ON bedrock_integration.bedrock_kb
        USING gin (to_tsvector('english', chunks));
    """)

    print("pgvector setup complete!")
    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup pgvector for Bedrock KB")
    parser.add_argument("--host", required=True, help="Aurora cluster endpoint")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--dbname", default="bedrockdb")
    parser.add_argument("--user", default="bedrock_admin")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    setup_pgvector(args.host, args.port, args.dbname, args.user, args.password)
