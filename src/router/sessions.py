"""Per-conversation session state backed by DynamoDB."""

from __future__ import annotations

import logging
import os
from enum import Enum

import boto3

logger = logging.getLogger(__name__)


class AgentMode(str, Enum):
    RAG = "rag"
    VENDING = "vending"


class SessionStore:
    """DynamoDB-backed session store.

    Table schema:
      PK (String) — conversation_id
    Attributes:
      agent (String) — "rag" or "vending"
    """

    def __init__(self, table_name: str | None = None) -> None:
        self._table_name = table_name or os.getenv("SESSION_TABLE_NAME", "teams-bot-sessions")
        self._table = boto3.resource("dynamodb").Table(self._table_name)

    def get(self, conversation_id: str) -> AgentMode | None:
        resp = self._table.get_item(Key={"PK": conversation_id})
        item = resp.get("Item")
        if item and "agent" in item:
            return AgentMode(item["agent"])
        return None

    def create(self, conversation_id: str, agent: AgentMode) -> None:
        self._table.put_item(Item={"PK": conversation_id, "agent": agent.value})

    def delete(self, conversation_id: str) -> None:
        self._table.delete_item(Key={"PK": conversation_id})
