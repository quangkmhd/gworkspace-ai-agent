"""Risk evaluator — rule-based risk assessment using configs/risk_policy.yaml."""

from __future__ import annotations

from typing import Any

import structlog

from backend.schemas.common import RiskLevel
from backend.services.policy_service import PolicyService

logger = structlog.get_logger("risk_evaluator")


class RiskEvaluator:
    """Evaluates risk for agent actions based on policy config.

    Rules:
      - Read-only → Low
      - Reversible write → Medium
      - Send/share/delete/critical overwrite → High
    """

    def __init__(self) -> None:
        self._policy = PolicyService()

    def evaluate(self, tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate risk for a tool invocation.

        Returns:
            dict with risk_level, requires_approval, reason
        """
        risk_level = self._policy.get_risk_level(tool_name)
        requires_approval = self._policy.requires_hitl(tool_name)
        reason = self._build_reason(tool_name, risk_level, args or {})

        return {
            "risk_level": risk_level,
            "requires_approval": requires_approval,
            "reason": reason,
        }

    def _build_reason(self, tool_name: str, risk: RiskLevel, args: dict[str, Any]) -> str:
        """Build a human-readable reason for the risk assessment."""
        action_type = tool_name.split(".")[-1] if "." in tool_name else tool_name

        if risk == RiskLevel.HIGH:
            if "send" in action_type:
                recipients = args.get("to", [])
                return f"Sending email to {len(recipients)} recipient(s) is irreversible"
            if "share" in action_type:
                return f"Sharing with external users requires approval"
            if "delete" in action_type:
                return f"Deletion is irreversible and requires approval"
            return f"{tool_name} is high risk and requires approval"

        if risk == RiskLevel.MEDIUM:
            return f"{tool_name} modifies data (reversible write)"

        return f"{tool_name} is read-only (safe to auto-execute)"

    def evaluate_batch(
        self, steps: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Evaluate risk for a batch of planned steps."""
        results = []
        for step in steps:
            tool = step.get("tool", "")
            args = step.get("args", {})
            result = self.evaluate(tool, args)
            result["step"] = step.get("step", 0)
            result["tool"] = tool
            results.append(result)
        return results
