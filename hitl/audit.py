"""HITL audit logging — structured audit trail for all approval decisions."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

import structlog

from backend.config import get_settings
from backend.schemas.common import generate_id

logger = structlog.get_logger("hitl.audit")


class AuditEntry:
    """Represents a single audit log entry."""

    def __init__(
        self,
        event_type: str,
        task_id: str = "",
        action_id: str = "",
        approval_id: str = "",
        actor: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_id = generate_id("aud")
        self.event_type = event_type
        self.task_id = task_id
        self.action_id = action_id
        self.approval_id = approval_id
        self.actor = actor
        self.details = details or {}
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "event_type": self.event_type,
            "task_id": self.task_id,
            "action_id": self.action_id,
            "approval_id": self.approval_id,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class AuditLogger:
    """Structured audit log storage backed by SQLite."""

    def __init__(self) -> None:
        settings = get_settings()
        self._db_path = settings.data_dir / "audit.db"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    task_id TEXT,
                    action_id TEXT,
                    approval_id TEXT,
                    actor TEXT,
                    details JSON,
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_logs(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_approval ON audit_logs(approval_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")

    def log(self, entry: AuditEntry) -> None:
        """Write an audit log entry."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT INTO audit_logs
                   (audit_id, event_type, task_id, action_id, approval_id, actor, details, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.audit_id,
                    entry.event_type,
                    entry.task_id,
                    entry.action_id,
                    entry.approval_id,
                    entry.actor,
                    json.dumps(entry.details),
                    entry.timestamp,
                ),
            )
        logger.info("audit_logged", audit_id=entry.audit_id, event_type=entry.event_type)

    def log_event(
        self,
        event_type: str,
        task_id: str = "",
        action_id: str = "",
        approval_id: str = "",
        actor: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Convenience method to create and log an entry."""
        entry = AuditEntry(
            event_type=event_type,
            task_id=task_id,
            action_id=action_id,
            approval_id=approval_id,
            actor=actor,
            details=details,
        )
        self.log(entry)
        return entry

    def query(
        self,
        task_id: str | None = None,
        action_id: str | None = None,
        approval_id: str | None = None,
        event_type: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit logs with filters."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: list[Any] = []

        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if action_id:
            query += " AND action_id = ?"
            params.append(action_id)
        if approval_id:
            query += " AND approval_id = ?"
            params.append(approval_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        if until:
            query += " AND timestamp <= ?"
            params.append(until)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "audit_id": r["audit_id"],
                "event_type": r["event_type"],
                "task_id": r["task_id"],
                "action_id": r["action_id"],
                "approval_id": r["approval_id"],
                "actor": r["actor"],
                "details": json.loads(r["details"]) if r["details"] else {},
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]

    def get_approval_trail(self, approval_id: str) -> list[dict[str, Any]]:
        """Get full audit trail for an approval."""
        return self.query(approval_id=approval_id)
