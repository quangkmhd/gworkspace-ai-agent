"""Tool registry — loads manifest, provides lookup, validates args via jsonschema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import structlog

from backend.config import get_settings
from tools.base import BaseTool, ToolDefinition

logger = structlog.get_logger("registry")


class ToolRegistry:
    """Central registry for all workspace tools.

    Loads tool definitions from configs/tool_manifest.json and
    maps them to concrete tool adapter implementations.
    """

    _instance: ToolRegistry | None = None

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._adapters: dict[str, BaseTool] = {}
        self._load_manifest()
        self._register_adapters()

    @classmethod
    def get(cls) -> ToolRegistry:
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def _load_manifest(self) -> None:
        """Load tool definitions from JSON manifest."""
        settings = get_settings()
        manifest_path = settings.configs_dir / "tool_manifest.json"
        if not manifest_path.exists():
            logger.warning("tool_manifest_not_found", path=str(manifest_path))
            return

        with open(manifest_path) as f:
            data = json.load(f)

        for tool_data in data.get("tools", []):
            defn = ToolDefinition(
                tool_name=tool_data["tool_name"],
                version=tool_data.get("version", "v1"),
                description=tool_data.get("description", ""),
                app=tool_data.get("app", ""),
                risk_level=tool_data.get("risk_level", "medium"),
                requires_hitl=tool_data.get("requires_hitl", False),
                oauth_scopes=tool_data.get("oauth_scopes", []),
                input_schema=tool_data.get("input_schema", {}),
                output_schema=tool_data.get("output_schema", {}),
            )
            self._definitions[defn.tool_name] = defn

        logger.info("manifest_loaded", tool_count=len(self._definitions))

    def _register_adapters(self) -> None:
        """Register concrete tool adapter instances."""
        from tools.gmail.adapter import (
            GmailCreateDraftTool,
            GmailGetMessageTool,
            GmailGetThreadTool,
            GmailSearchTool,
            GmailSendEmailTool,
        )
        from tools.calendar.adapter import (
            CalendarCreateEventTool,
            CalendarDeleteEventTool,
            CalendarGetCalendarsInfoTool,
            CalendarGetCurrentDatetimeTool,
            CalendarMoveEventTool,
            CalendarSearchEventsTool,
            CalendarUpdateEventTool,
        )
        from tools.sheets.adapter import (
            SheetsAppendValuesTool,
            SheetsBatchReadDataTool,
            SheetsBatchUpdateValuesTool,
            SheetsClearValuesTool,
            SheetsCreateSpreadsheetTool,
            SheetsFilteredReadDataTool,
            SheetsGetSpreadsheetInfoTool,
            SheetsReadDataTool,
            SheetsUpdateValuesTool,
        )
        from tools.drive.adapter import (
            DriveCopyFileTool,
            DriveDeleteFileTool,
            DriveExportFileTool,
            DriveGetFileContentTool,
            DriveMoveFileTool,
            DriveSearchFilesTool,
            DriveShareFileTool,
            DriveUploadFileTool,
        )
        from tools.docs.adapter import (
            DocsBatchUpdateTool,
            DocsCreateDocumentTool,
            DocsGetDocumentTool,
            DocsInsertTextTool,
            DocsReplaceTextTool,
            DocsShareDocumentTool,
        )

        adapters: list[BaseTool] = [
            # Gmail
            GmailSearchTool(), GmailGetMessageTool(), GmailGetThreadTool(),
            GmailCreateDraftTool(), GmailSendEmailTool(),
            # Calendar
            CalendarGetCalendarsInfoTool(), CalendarSearchEventsTool(),
            CalendarCreateEventTool(), CalendarUpdateEventTool(),
            CalendarMoveEventTool(), CalendarDeleteEventTool(),
            CalendarGetCurrentDatetimeTool(),
            # Sheets
            SheetsCreateSpreadsheetTool(), SheetsGetSpreadsheetInfoTool(),
            SheetsReadDataTool(), SheetsBatchReadDataTool(),
            SheetsFilteredReadDataTool(), SheetsUpdateValuesTool(),
            SheetsAppendValuesTool(), SheetsClearValuesTool(),
            SheetsBatchUpdateValuesTool(),
            # Drive
            DriveSearchFilesTool(), DriveUploadFileTool(), DriveMoveFileTool(),
            DriveCopyFileTool(), DriveShareFileTool(), DriveDeleteFileTool(),
            DriveExportFileTool(), DriveGetFileContentTool(),
            # Docs (custom)
            DocsCreateDocumentTool(), DocsGetDocumentTool(), DocsBatchUpdateTool(),
            DocsInsertTextTool(), DocsReplaceTextTool(), DocsShareDocumentTool(),
        ]

        for adapter in adapters:
            self._adapters[adapter.name] = adapter

        logger.info("adapters_registered", count=len(self._adapters))

    def list_tools(self) -> list[ToolDefinition]:
        """Return all tool definitions."""
        return list(self._definitions.values())

    def get_tool(self, tool_name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self._definitions.get(tool_name)

    def get_adapter(self, tool_name: str) -> BaseTool | None:
        """Get a tool adapter by name."""
        return self._adapters.get(tool_name)

    def validate_args(self, tool_name: str, args: dict[str, Any]) -> list[str]:
        """Validate tool arguments against the input schema.

        Returns list of validation error messages (empty = valid).
        """
        defn = self._definitions.get(tool_name)
        if not defn or not defn.input_schema:
            return []

        try:
            jsonschema.validate(instance=args, schema=defn.input_schema)
            return []
        except jsonschema.ValidationError as e:
            return [e.message]
        except jsonschema.SchemaError as e:
            return [f"Invalid schema: {e.message}"]

    def invoke(
        self, tool_name: str, args: dict[str, Any], credentials: Any = None
    ) -> dict[str, Any]:
        """Validate args and invoke a tool.

        Raises ValueError if tool not found or validation fails.
        """
        adapter = self.get_adapter(tool_name)
        if not adapter:
            raise ValueError(f"Tool not found: {tool_name}")

        errors = self.validate_args(tool_name, args)
        if errors:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")

        return adapter.run(args, credentials)
