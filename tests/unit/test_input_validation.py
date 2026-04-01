"""Unit tests for input validation."""

from __future__ import annotations

from tools.registry import ToolRegistry


class TestInputValidation:
    def setup_method(self):
        ToolRegistry.reset()
        self.registry = ToolRegistry.get()

    def test_valid_gmail_search(self):
        errors = self.registry.validate_args("gmail.search", {"query": "test"})
        assert errors == []

    def test_missing_required_field(self):
        errors = self.registry.validate_args("gmail.search", {})
        assert len(errors) > 0
        assert "query" in errors[0].lower() or "required" in errors[0].lower()

    def test_valid_calendar_create(self):
        args = {
            "calendar_id": "primary",
            "summary": "Meeting",
            "start": "2024-01-15T10:00:00",
            "end": "2024-01-15T11:00:00",
        }
        errors = self.registry.validate_args("calendar.create_event", args)
        assert errors == []

    def test_invalid_extra_type(self):
        """Max results with wrong type."""
        args = {"query": "test", "max_results": "not_a_number"}
        errors = self.registry.validate_args("gmail.search", args)
        assert len(errors) > 0

    def test_unknown_tool(self):
        errors = self.registry.validate_args("nonexistent.tool", {})
        assert errors == []  # Unknown tools skip validation

    def test_valid_sheets_read(self):
        args = {"spreadsheet_id": "abc123", "range": "Sheet1!A1:C10"}
        errors = self.registry.validate_args("sheets.read_data", args)
        assert errors == []
