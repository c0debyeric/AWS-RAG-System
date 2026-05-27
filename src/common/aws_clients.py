"""Boto3 client factories with lazy initialization."""

import json

import boto3
from functools import lru_cache


@lru_cache
def get_bedrock_runtime():
    return boto3.client("bedrock-runtime")


@lru_cache
def get_s3():
    return boto3.client("s3")


@lru_cache
def get_secretsmanager():
    return boto3.client("secretsmanager")


def get_db_credentials(secret_arn: str) -> dict:
    """Retrieve database credentials from Secrets Manager."""
    client = get_secretsmanager()
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])
