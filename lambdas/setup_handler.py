"""One-time Lambda handler that initializes the pgvector schema.

This Lambda runs inside the VPC so it can reach the private Aurora cluster.
Terraform invokes it once after the database stack is created.
"""
import json
import logging
import os

import boto3

from setup_pgvector import setup_pgvector


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Fetch Aurora credentials from Secrets Manager and create the schema."""
    secret_arn = os.environ["DB_SECRET_ARN"]
    secretsmanager = boto3.client("secretsmanager")

    response = secretsmanager.get_secret_value(SecretId=secret_arn)
    credentials = json.loads(response["SecretString"])

    host = credentials["host"]
    port = int(credentials.get("port", 5432))
    dbname = credentials["dbname"]
    user = credentials["username"]
    password = credentials["password"]

    logger.info("Running pgvector schema bootstrap against %s:%s/%s", host, port, dbname)
    setup_pgvector(host=host, port=port, dbname=dbname, user=user, password=password)

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "message": "pgvector schema initialized"}),
    }