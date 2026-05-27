"""Configuration from environment variables."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))

    # Bedrock models
    embedding_model_id: str = field(
        default_factory=lambda: os.environ.get("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
    )
    generation_model_id: str = field(
        default_factory=lambda: os.environ.get("GENERATION_MODEL_ID", "anthropic.claude-sonnet-4-6")
    )

    # Database
    db_host: str = field(default_factory=lambda: os.environ.get("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.environ.get("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.environ.get("DB_NAME", "ragdb"))
    db_user: str = field(default_factory=lambda: os.environ.get("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.environ.get("DB_PASSWORD", ""))
    db_secret_arn: str = field(default_factory=lambda: os.environ.get("DB_SECRET_ARN", ""))

    # S3
    documents_bucket: str = field(default_factory=lambda: os.environ.get("DOCUMENTS_BUCKET", ""))

    # Retrieval tuning
    top_k: int = field(default_factory=lambda: int(os.environ.get("TOP_K", "5")))
    chunk_size: int = field(default_factory=lambda: int(os.environ.get("CHUNK_SIZE", "512")))
    chunk_overlap: int = field(default_factory=lambda: int(os.environ.get("CHUNK_OVERLAP", "100")))

    # Titan Embed Text v2 = 1024 dimensions
    embedding_dim: int = field(default_factory=lambda: int(os.environ.get("EMBEDDING_DIM", "1024")))


_config = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
