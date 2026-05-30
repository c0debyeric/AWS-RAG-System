"""Adaptive Card JSON builders for the bot router."""

from __future__ import annotations


def build_mode_selector_card() -> dict:
    """Card shown on first message — user picks an agent mode."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Welcome! What can I help you with?",
                "size": "Large",
                "weight": "Bolder",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": "Pick a mode to get started.  Type **menu** at any time to switch.",
                "wrap": True,
                "spacing": "Small",
            },
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "📚  Knowledge Base",
                                "weight": "Bolder",
                                "horizontalAlignment": "Center",
                            },
                            {
                                "type": "TextBlock",
                                "text": "Ask questions about internal docs, runbooks, and procedures.",
                                "wrap": True,
                                "size": "Small",
                                "horizontalAlignment": "Center",
                            },
                            {
                                "type": "ActionSet",
                                "actions": [
                                    {
                                        "type": "Action.Submit",
                                        "title": "Knowledge Base",
                                        "data": {"action": "select_agent", "agent": "rag"},
                                        "style": "positive",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "☁️  AWS Account Setup",
                                "weight": "Bolder",
                                "horizontalAlignment": "Center",
                            },
                            {
                                "type": "TextBlock",
                                "text": "Provision a new AWS account or configure an existing one.",
                                "wrap": True,
                                "size": "Small",
                                "horizontalAlignment": "Center",
                            },
                            {
                                "type": "ActionSet",
                                "actions": [
                                    {
                                        "type": "Action.Submit",
                                        "title": "Account Setup",
                                        "data": {"action": "select_agent", "agent": "vending"},
                                        "style": "positive",
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
