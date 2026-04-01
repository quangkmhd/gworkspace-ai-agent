"""Drive tool adapters — Google Drive API for file operations.

8 tools: search, upload, move, copy, share, delete, export, get_content.
Search uses LangChain GoogleDriveSearchTool where available; others use
google-api-python-client directly.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import structlog

from tools.base import BaseTool

logger = structlog.get_logger("tools.drive")


def _build_drive_service(credentials: Any) -> Any:
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=credentials)


class DriveSearchFilesTool(BaseTool):
    name = "drive.search_files"
    description = "Search files in Google Drive"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        q = args["query"]
        if args.get("folder_id"):
            q += f" and '{args['folder_id']}' in parents"
        results = service.files().list(
            q=q,
            pageSize=args.get("page_size", 20),
            fields="files(id, name, mimeType, modifiedTime, size)",
        ).execute()
        return {"files": results.get("files", [])}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "files": [
                {"id": "mock_file_001", "name": f"Result for: {args.get('query', '')}", "mimeType": "application/pdf"},
                {"id": "mock_file_002", "name": "Report.docx", "mimeType": "application/vnd.google-apps.document"},
            ]
        }


class DriveUploadFileTool(BaseTool):
    name = "drive.upload_file"
    description = "Upload file to Drive"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        from googleapiclient.http import MediaInMemoryUpload
        service = _build_drive_service(credentials)
        content = base64.b64decode(args["content_base64"])
        metadata: dict[str, Any] = {"name": args["name"]}
        if args.get("folder_id"):
            metadata["parents"] = [args["folder_id"]]
        media = MediaInMemoryUpload(content, mimetype=args.get("mime_type", "application/octet-stream"))
        result = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return {"file_id": result["id"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"file_id": "mock_uploaded_001", "name": args.get("name", "file.txt")}


class DriveMoveFileTool(BaseTool):
    name = "drive.move_file"
    description = "Move file between folders"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        file_id = args["file_id"]
        file = service.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        service.files().update(
            fileId=file_id,
            addParents=args["target_folder_id"],
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
        return {"file_id": file_id, "moved": True}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"file_id": args.get("file_id", "mock"), "moved": True}


class DriveCopyFileTool(BaseTool):
    name = "drive.copy_file"
    description = "Copy a Drive file"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        body: dict[str, Any] = {}
        if args.get("new_name"):
            body["name"] = args["new_name"]
        if args.get("target_folder_id"):
            body["parents"] = [args["target_folder_id"]]
        result = service.files().copy(fileId=args["file_id"], body=body).execute()
        return {"file_id": result["id"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"file_id": "mock_copy_001"}


class DriveShareFileTool(BaseTool):
    name = "drive.share_file"
    description = "Share file with user/domain"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        permission: dict[str, Any] = {"type": args["type"], "role": args["role"]}
        if args.get("email"):
            permission["emailAddress"] = args["email"]
        if args.get("domain"):
            permission["domain"] = args["domain"]
        service.permissions().create(fileId=args["file_id"], body=permission).execute()
        return {"shared": True, "file_id": args["file_id"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"shared": True, "file_id": args.get("file_id", "mock")}


class DriveDeleteFileTool(BaseTool):
    name = "drive.delete_file"
    description = "Delete a Drive file"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        service.files().delete(fileId=args["file_id"]).execute()
        return {"deleted": True}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"deleted": True, "file_id": args.get("file_id", "mock")}


class DriveExportFileTool(BaseTool):
    name = "drive.export_file"
    description = "Export Google file to target MIME"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        content = service.files().export(fileId=args["file_id"], mimeType=args["mime_type"]).execute()
        encoded = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
        return {"content_base64": encoded}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"content_base64": base64.b64encode(b"Mock exported content").decode()}


class DriveGetFileContentTool(BaseTool):
    name = "drive.get_file_content"
    description = "Get normalized file content"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_drive_service(credentials)
        # Try to get metadata first to determine type
        file_meta = service.files().get(fileId=args["file_id"], fields="mimeType,name").execute()
        mime = file_meta.get("mimeType", "")
        if mime.startswith("application/vnd.google-apps"):
            # Google Workspace file → export as text
            content = service.files().export(fileId=args["file_id"], mimeType="text/plain").execute()
            text = content.decode() if isinstance(content, bytes) else str(content)
        else:
            content = service.files().get_media(fileId=args["file_id"]).execute()
            text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else str(content)
        return {"content": text, "name": file_meta.get("name", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"content": "Mock file content for testing.", "name": "mock_file.txt"}
