"""Abstract base tool and tool registration types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog
from pydantic import BaseModel

from backend.config import get_settings
from backend.schemas.common import RiskLevel

logger = structlog.get_logger("tools")


class ToolDefinition(BaseModel):
    """Tool metadata from the tool manifest."""

    tool_name: str
    version: str = "v1"
    description: str = ""
    app: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_hitl: bool = False
    oauth_scopes: list[str] = []
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract base class for all workspace tool adapters."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        """Execute the tool with given arguments.

        Args:
            args: Validated arguments matching the tool's input schema.
            credentials: Google OAuth credentials for API calls.

        Returns:
            Result dict matching the tool's output schema.
        """
        ...

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic mock data for testing without credentials."""
        return {"mock": True, "tool": self.name, "args": args}

    def run(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        """Execute or mock based on MOCK_MODE setting."""
        settings = get_settings()
        if settings.MOCK_MODE:
            logger.info("tool_mock_execute", tool=self.name)
            return self.mock_execute(args)
        logger.info("tool_execute", tool=self.name)
        return self.execute(args, credentials)
