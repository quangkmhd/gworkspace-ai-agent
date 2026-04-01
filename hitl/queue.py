"""HITL (Human-in-the-Loop) approval queue — in-memory + SQLite backed."""

from __future__ import annotations

import sqlite3
import json
import time
from typing import Any

import structlog

from backend.config import get_settings
from backend.schemas.action import ApprovalPayload
from backend.schemas.common import ApprovalStatus

logger = structlog.get_logger("hitl.queue")


class ApprovalQueue:
    """HITL approval queue backed by SQLite.

    Stores approval proposals and manages their lifecycle.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._db_path = settings.data_dir / "hitl.db"
        self._timeout = settings.HITL_APPROVAL_TIMEOUT_SECONDS
        self._init_db()
        # In-memory cache for fast access
        self._cache: dict[str, ApprovalPayload] = {}

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    payload JSON NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    decided_at REAL,
                    decided_by TEXT,
                    expires_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_user ON approvals(user_id)")

    def create(self, proposal: ApprovalPayload) -> ApprovalPayload:
        """Add a new approval proposal to the queue."""
        if not proposal.expires_at:
            proposal.expires_at = time.time() + self._timeout
        now = time.time()

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT INTO approvals
                   (approval_id, task_id, user_id, status, payload, created_at, updated_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    proposal.approval_id,
                    proposal.task_id,
                    proposal.user_id,
                    proposal.status.value,
                    json.dumps(proposal.model_dump(), default=str),
                    now,
                    now,
                    proposal.expires_at,
                ),
            )

        self._cache[proposal.approval_id] = proposal
        logger.info("approval_created", approval_id=proposal.approval_id, task_id=proposal.task_id)
        return proposal

    def get(self, approval_id: str) -> ApprovalPayload | None:
        """Get approval by ID."""
        if approval_id in self._cache:
            return self._cache[approval_id]

        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        proposal = ApprovalPayload(**data)
        self._cache[approval_id] = proposal
        return proposal

    def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_by: str = "",
        edited_args: dict[str, Any] | None = None,
        reason: str = "",
    ) -> ApprovalPayload | None:
        """Update the status of an approval."""
        proposal = self.get(approval_id)
        if not proposal:
            return None

        now = time.time()
        proposal.status = status
        proposal.decided_at = now
        proposal.decided_by = decided_by
        proposal.updated_at = now
        if edited_args:
            proposal.edited_args = edited_args
        if reason:
            proposal.reason = reason

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """UPDATE approvals
                   SET status = ?, payload = ?, updated_at = ?, decided_at = ?, decided_by = ?
                   WHERE approval_id = ?""",
                (
                    status.value,
                    json.dumps(proposal.model_dump(), default=str),
                    now,
                    now,
                    decided_by,
                    approval_id,
                ),
            )

        self._cache[approval_id] = proposal
        logger.info("approval_updated", approval_id=approval_id, status=status.value)
        return proposal

    def list_approvals(
        self,
        user_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 50,
    ) -> list[ApprovalPayload]:
        """List approvals with optional filters."""
        query = "SELECT payload FROM approvals WHERE 1=1"
        params: list[Any] = []
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, params).fetchall()

        return [ApprovalPayload(**json.loads(r[0])) for r in rows]

    def expire_stale(self) -> int:
        """Expire approvals past their timeout."""
        now = time.time()
        with sqlite3.connect(self._db_path) as conn:
            stale_rows = conn.execute(
                """SELECT approval_id, payload FROM approvals
                   WHERE status = 'pending' AND expires_at < ?""",
                (now,),
            ).fetchall()
            for approval_id, payload in stale_rows:
                data = json.loads(payload)
                data["status"] = ApprovalStatus.EXPIRED.value
                data["updated_at"] = now
                conn.execute(
                    """UPDATE approvals
                       SET status = ?, payload = ?, updated_at = ?
                       WHERE approval_id = ?""",
                    (
                        ApprovalStatus.EXPIRED.value,
                        json.dumps(data, default=str),
                        now,
                        approval_id,
                    ),
                )
        expired = len(stale_rows)
        if expired:
            logger.info("approvals_expired", count=expired)
            # Clear cache for expired items
            for k in list(self._cache):
                if self._cache[k].status == ApprovalStatus.PENDING:
                    expires_at = self._cache[k].expires_at
                    if expires_at is not None and expires_at < now:
                        self._cache[k].status = ApprovalStatus.EXPIRED
        return expired
