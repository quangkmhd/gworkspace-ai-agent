"""Integration tests for tool invoke flow."""

from __future__ import annotations

from backend.services.tool_invoke_service import ToolInvokeService
from tools.registry import ToolRegistry


class TestToolInvokeFlow:
    def setup_method(self):
        ToolRegistry.reset()
        self.service = ToolInvokeService()

    def test_invoke_low_risk_tool(self):
        """Low risk tool should auto-execute."""
        result = self.service.invoke("gmail.search", {"query": "test"})
        assert result["status"] == "completed"
        assert "result" in result

    def test_invoke_high_risk_returns_pending(self):
        """High risk tool should return pending_approval."""
        result = self.service.invoke(
            "gmail.send_email",
            {"to": ["test@test.com"], "subject": "Test", "body": "Test body"},
        )
        assert result["status"] == "pending_approval"
        assert "approval" in result

    def test_invoke_dry_run(self):
        """Dry run returns preview without executing."""
        result = self.service.invoke(
            "gmail.search",
            {"query": "test"},
            dry_run=True,
        )
        assert result["status"] == "preview"
        assert "action" in result
        assert "preview" in result

    def test_invoke_unknown_tool(self):
        """Unknown tool raises ValueError."""
        try:
            self.service.invoke("nonexistent.tool", {})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown tool" in str(e)

    def test_invoke_invalid_args(self):
        """Invalid args raises ValueError."""
        try:
            self.service.invoke("gmail.search", {})  # Missing required 'query'
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid args" in str(e)

    def test_invoke_medium_risk_auto_execute(self):
        """Medium risk tool without HITL config should auto-execute."""
        result = self.service.invoke(
            "gmail.create_draft",
            {"to": ["test@test.com"], "subject": "Draft", "body": "Draft body"},
        )
        assert result["status"] == "completed"
