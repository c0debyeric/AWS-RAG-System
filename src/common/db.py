"""Database connection management for pgvector."""

import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from common.config import get_config
from common.aws_clients import get_db_credentials


_connection = None


def get_connection():
    """Get or create a database connection with pgvector support."""
    global _connection
    if _connection is not None and not _connection.closed:
        return _connection

    config = get_config()

    if config.db_secret_arn:
        creds = get_db_credentials(config.db_secret_arn)
        host = creds.get("host", config.db_host)
        port = int(creds.get("port", config.db_port))
        dbname = creds.get("dbname", config.db_name)
        user = creds.get("username", config.db_user)
        password = creds["password"]
    else:
        host = config.db_host
        port = config.db_port
        dbname = config.db_name
        user = config.db_user
        password = config.db_password

    _connection = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    _connection.autocommit = True
    register_vector(_connection)

    return _connection


def execute_query(query: str, params=None, fetch: bool = True):
    """Execute a query and optionally return results as dicts."""
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
