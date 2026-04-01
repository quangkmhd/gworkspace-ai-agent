"""E2E test: Read sheet → create draft → approve → send email."""

from __future__ import annotations

from tools.registry import ToolRegistry


class TestSheetToEmail:
    def test_full_flow(self, client):
        """E2E: sheet read → draft → (approval needed for send)."""
        ToolRegistry.reset()

        # Step 1: Read sheet data (low risk, auto-execute)
        resp = client.post(
            "/v1/tools/sheets.read_data/invoke",
            json={
                "task_id": "tsk_e2e_001",
                "actor": "user_test",
                "args": {"spreadsheet_id": "ss_001", "range": "Sheet1!A1:C10"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "completed"

        # Step 2: Create email draft (medium risk, auto-execute)
        resp = client.post(
            "/v1/tools/gmail.create_draft/invoke",
            json={
                "task_id": "tsk_e2e_001",
                "actor": "user_test",
                "args": {
                    "to": ["team@company.com"],
                    "subject": "Weekly Report",
                    "body": "Here is the weekly data...",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "completed"

        # Step 3: Send email (high risk, needs approval)
        resp = client.post(
            "/v1/tools/gmail.send_email/invoke",
            json={
                "task_id": "tsk_e2e_001",
                "actor": "user_test",
                "args": {
                    "to": ["team@company.com"],
                    "subject": "Weekly Report",
                    "body": "Here is the weekly data...",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "pending_approval"
