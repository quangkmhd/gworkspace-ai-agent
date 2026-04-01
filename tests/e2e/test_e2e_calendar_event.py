"""E2E test: Create calendar event → policy check."""

from __future__ import annotations

from tools.registry import ToolRegistry


class TestCalendarEvent:
    def test_create_event_auto_approved(self, client):
        """Calendar event creation is medium risk → auto-execute."""
        ToolRegistry.reset()

        resp = client.post(
            "/v1/tools/calendar.create_event/invoke",
            json={
                "task_id": "tsk_e2e_cal",
                "actor": "user_test",
                "args": {
                    "calendar_id": "primary",
                    "summary": "Team Standup",
                    "start": "2024-01-16T09:00:00+07:00",
                    "end": "2024-01-16T09:15:00+07:00",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "completed"

    def test_delete_event_needs_approval(self, client):
        """Calendar event deletion is high risk → pending approval."""
        ToolRegistry.reset()

        resp = client.post(
            "/v1/tools/calendar.delete_event/invoke",
            json={
                "task_id": "tsk_e2e_cal",
                "actor": "user_test",
                "args": {"calendar_id": "primary", "event_id": "event_001"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "pending_approval"
