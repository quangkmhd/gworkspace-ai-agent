"""Docs tool adapters — custom adapter using Google Docs API directly.

No LangChain toolkit for Docs exists, so we use google-api-python-client.
6 tools: create, get, batch_update, insert_text, replace_text, share.
"""

from __future__ import annotations

from typing import Any

import structlog

from tools.base import BaseTool

logger = structlog.get_logger("tools.docs")


def _build_docs_service(credentials: Any) -> Any:
    from googleapiclient.discovery import build
    return build("docs", "v1", credentials=credentials)


def _build_drive_service(credentials: Any) -> Any:
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=credentials)


class DocsCreateDocumentTool(BaseTool):
    name = "docs.create_document"
    description = "Create Google Doc"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_docs_service(credentials)
        result = service.documents().create(body={"title": args["title"]}).execute()
        return {"document_id": result["documentId"], "title": result.get("title", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"document_id": "mock_doc_001", "title": args.get("title", "")}


class DocsGetDocumentTool(BaseTool):
    name = "docs.get_document"
    description = "Get Google Doc content"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_docs_service(credentials)
        doc = service.documents().get(documentId=args["document_id"]).execute()
        # Extract plain text from doc body
        content_parts = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph", {})
            for pe in paragraph.get("elements", []):
                text_run = pe.get("textRun", {})
                if text_run.get("content"):
                    content_parts.append(text_run["content"])
        return {
            "document_id": doc["documentId"],
            "title": doc.get("title", ""),
            "content": "".join(content_parts),
        }

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "document_id": args.get("document_id", "mock_doc"),
            "title": "Mock Document",
            "content": "This is the mock document content.",
        }


class DocsBatchUpdateTool(BaseTool):
    name = "docs.batch_update"
    description = "Batch update Google Doc"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_docs_service(credentials)
        service.documents().batchUpdate(
            documentId=args["document_id"],
            body={"requests": args["requests"]},
        ).execute()
        return {"applied": True, "document_id": args["document_id"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"applied": True, "document_id": args.get("document_id", "mock")}


class DocsInsertTextTool(BaseTool):
    name = "docs.insert_text"
    description = "Insert text into Google Doc"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_docs_service(credentials)
        requests = [
            {"insertText": {"location": {"index": args["index"]}, "text": args["text"]}}
        ]
        service.documents().batchUpdate(
            documentId=args["document_id"],
            body={"requests": requests},
        ).execute()
        return {"inserted": True, "document_id": args["document_id"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"inserted": True, "document_id": args.get("document_id", "mock")}


class DocsReplaceTextTool(BaseTool):
    name = "docs.replace_text"
    description = "Replace text in Google Doc"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_docs_service(credentials)
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": args["search_text"], "matchCase": True},
                    "replaceText": args["replace_text"],
                }
            }
        ]
        result = service.documents().batchUpdate(
            documentId=args["document_id"],
            body={"requests": requests},
        ).execute()
        replies = result.get("replies", [{}])
        occurrences = replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0) if replies else 0
        return {"replaced": True, "occurrences_changed": occurrences}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"replaced": True, "occurrences_changed": 1}


class DocsShareDocumentTool(BaseTool):
    name = "docs.share_document"
    description = "Share Google Doc via Drive permission"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        drive = _build_drive_service(credentials)
        permission = {
            "type": "user",
            "role": args["role"],
            "emailAddress": args["email"],
        }
        drive.permissions().create(
            fileId=args["document_id"], body=permission, sendNotificationEmail=True
        ).execute()
        return {"shared": True, "document_id": args["document_id"], "email": args["email"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"shared": True, "document_id": args.get("document_id", "mock"), "email": args.get("email", "user@ex.com")}
