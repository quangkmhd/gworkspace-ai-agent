"""Authorization policy service — checks scopes, risk level, HITL requirements."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from backend.config import get_settings
from backend.schemas.common import RiskLevel

logger = structlog.get_logger("policy")


class PolicyService:
    """Evaluates authorization and risk policies before tool execution."""

    def __init__(self) -> None:
        settings = get_settings()
        self._risk_policy = self._load_yaml(settings.configs_dir / "risk_policy.yaml")
        self._oauth_scopes = self._load_yaml(settings.configs_dir / "oauth_scopes.yaml")
        self._always_hitl = set(self._risk_policy.get("always_hitl_actions", []))

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_risk_level(self, tool_name: str) -> RiskLevel:
        """Get the configured risk level for a tool."""
        levels = self._risk_policy.get("risk_levels", {})
        tool_config = levels.get(tool_name, {})
        risk_str = tool_config.get("risk", "medium")
        try:
            return RiskLevel(risk_str)
        except ValueError:
            return RiskLevel.MEDIUM

    def requires_hitl(self, tool_name: str) -> bool:
        """Check if a tool requires HITL approval.

        Rules:
          1. If tool action type is in always_hitl_actions → True
          2. If tool is explicitly configured → use config
          3. High risk → True (safety default)
        """
        # Check always-HITL action types
        action_type = tool_name.split(".")[-1] if "." in tool_name else ""
        for always_action in self._always_hitl:
            if always_action in action_type:
                return True

        levels = self._risk_policy.get("risk_levels", {})
        tool_config = levels.get(tool_name, {})

        if "requires_hitl" in tool_config:
            return bool(tool_config["requires_hitl"])

        # Default: high risk requires HITL
        return self.get_risk_level(tool_name) == RiskLevel.HIGH

    def get_required_scopes(self, tool_name: str) -> list[str]:
        """Get required OAuth scopes for a tool."""
        scopes = self._oauth_scopes.get("scopes", {})
        return scopes.get(tool_name, [])

    def check_scopes(self, tool_name: str, granted_scopes: list[str]) -> bool:
        """Verify user has granted all required scopes for a tool."""
        required = self.get_required_scopes(tool_name)
        if not required:
            return True
        return all(scope in granted_scopes for scope in required)

    def evaluate(
        self, tool_name: str, granted_scopes: list[str] | None = None
    ) -> dict[str, Any]:
        """Full policy evaluation for a tool invocation.

        Returns dict with: risk_level, requires_approval, scopes_ok, reason.
        """
        risk = self.get_risk_level(tool_name)
        needs_hitl = self.requires_hitl(tool_name)
        scopes_ok = True
        reason = ""

        if granted_scopes is not None:
            scopes_ok = self.check_scopes(tool_name, granted_scopes)
            if not scopes_ok:
                reason = f"Missing required OAuth scopes for {tool_name}"

        if needs_hitl:
            reason = reason or f"{tool_name} is {risk.value} risk and requires approval"

        return {
            "risk_level": risk,
            "requires_approval": needs_hitl,
            "scopes_ok": scopes_ok,
            "reason": reason,
        }
