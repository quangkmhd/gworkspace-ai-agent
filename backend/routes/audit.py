"""Audit endpoints — query audit logs."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.schemas.envelope import ResponseEnvelope
from hitl.audit import AuditLogger

router = APIRouter(prefix="/v1/audit", tags=["Audit"])


@router.get("/logs")
async def query_logs(
    task_id: str | None = Query(None),
    action_id: str | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> ResponseEnvelope:
    """GET /v1/audit/logs — Query audit logs."""
    audit = AuditLogger()
    logs = audit.query(
        task_id=task_id,
        action_id=action_id,
        event_type=event_type,
        limit=limit,
    )
    return ResponseEnvelope.success(data={"logs": logs, "total": len(logs)})


@router.get("/approvals/{approval_id}")
async def approval_trail(approval_id: str) -> ResponseEnvelope:
    """GET /v1/audit/approvals/{approval_id} — Full approval audit trail."""
    audit = AuditLogger()
    trail = audit.get_approval_trail(approval_id)
    return ResponseEnvelope.success(data={"trail": trail, "total": len(trail)})
