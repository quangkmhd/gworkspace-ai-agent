"""Gmail tool adapters — wraps LangChain GmailToolkit tools.

Uses langchain_google_community.GmailToolkit for:
  - GmailSearch, GmailGetMessage, GmailGetThread, GmailCreateDraft, GmailSendMessage
"""

from __future__ import annotations

from typing import Any

import structlog
from google.oauth2.credentials import Credentials

from tools.base import BaseTool

logger = structlog.get_logger("tools.gmail")


def _build_gmail_toolkit(credentials: Credentials) -> Any:
    """Build LangChain GmailToolkit with user credentials."""
    from langchain_google_community import GmailToolkit
    from langchain_google_community.gmail.utils import (
        build_resource_service,
        get_gmail_credentials,
    )

    api_resource = build_resource_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    return toolkit


def _get_tool_from_toolkit(toolkit: Any, tool_name: str) -> Any:
    """Get a specific tool from the GmailToolkit by name."""
    tools = toolkit.get_tools()
    for t in tools:
        if t.name == tool_name:
            return t
    raise ValueError(f"Tool '{tool_name}' not found in GmailToolkit")


class GmailSearchTool(BaseTool):
    name = "gmail.search"
    description = "Search Gmail messages by query"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        toolkit = _build_gmail_toolkit(credentials)
        tool = _get_tool_from_toolkit(toolkit, "search_gmail")
        query = args.get("query", "")
        max_results = args.get("max_results", 10)
        result = tool.invoke({"query": query, "max_results": max_results})
        logger.info("gmail_search_executed", query=query)
        return {"messages": result if isinstance(result, list) else [result]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "messages": [
                {
                    "id": "mock_msg_001",
                    "threadId": "mock_thread_001",
                    "snippet": f"Mock result for query: {args.get('query', '')}",
                    "from": "sender@example.com",
                    "to": "user@example.com",
                    "subject": "Mock Email Subject",
                    "date": "2024-01-15T10:30:00Z",
                },
            ]
        }


class GmailGetMessageTool(BaseTool):
    name = "gmail.get_message"
    description = "Get a Gmail message detail"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        toolkit = _build_gmail_toolkit(credentials)
        tool = _get_tool_from_toolkit(toolkit, "get_gmail_message")
        message_id = args["message_id"]
        result = tool.invoke({"message_id": message_id})
        logger.info("gmail_get_message_executed", message_id=message_id)
        return result if isinstance(result, dict) else {"content": str(result)}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": args.get("message_id", "mock_msg"),
            "threadId": "mock_thread_001",
            "from": "sender@example.com",
            "to": "user@example.com",
            "subject": "Mock Message Detail",
            "body": "This is a mock message body content.",
            "date": "2024-01-15T10:30:00Z",
        }


class GmailGetThreadTool(BaseTool):
    name = "gmail.get_thread"
    description = "Get a Gmail thread"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        toolkit = _build_gmail_toolkit(credentials)
        tool = _get_tool_from_toolkit(toolkit, "get_gmail_thread")
        thread_id = args["thread_id"]
        result = tool.invoke({"thread_id": thread_id})
        logger.info("gmail_get_thread_executed", thread_id=thread_id)
        return result if isinstance(result, dict) else {"messages": [str(result)]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "thread_id": args.get("thread_id", "mock_thread"),
            "messages": [
                {
                    "id": "mock_msg_001",
                    "from": "sender@example.com",
                    "body": "First message in thread",
                },
                {
                    "id": "mock_msg_002",
                    "from": "user@example.com",
                    "body": "Reply in thread",
                },
            ],
        }


class GmailCreateDraftTool(BaseTool):
    name = "gmail.create_draft"
    description = "Create Gmail draft"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        toolkit = _build_gmail_toolkit(credentials)
        tool = _get_tool_from_toolkit(toolkit, "create_gmail_draft")
        result = tool.invoke({
            "to": args.get("to", []),
            "subject": args.get("subject", ""),
            "message": args.get("body", ""),
            "cc": args.get("cc", []),
            "bcc": args.get("bcc", []),
        })
        logger.info("gmail_draft_created", to=args.get("to"))
        return {"draft_id": str(result)} if not isinstance(result, dict) else result

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "draft_id": "mock_draft_001",
            "to": args.get("to", []),
            "subject": args.get("subject", ""),
        }


class GmailSendEmailTool(BaseTool):
    name = "gmail.send_email"
    description = "Send Gmail message"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        toolkit = _build_gmail_toolkit(credentials)
        tool = _get_tool_from_toolkit(toolkit, "send_gmail_message")
        result = tool.invoke({
            "to": args.get("to", []),
            "subject": args.get("subject", ""),
            "message": args.get("body", ""),
            "cc": args.get("cc", []),
            "bcc": args.get("bcc", []),
        })
        logger.info("gmail_email_sent", to=args.get("to"))
        return {"message_id": str(result)} if not isinstance(result, dict) else result

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "message_id": "mock_sent_001",
            "to": args.get("to", []),
            "subject": args.get("subject", ""),
            "status": "sent",
        }
