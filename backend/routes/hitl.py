"""HITL approval and proposal endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.local_identity import get_local_user_id
from backend.schemas.action import EditApproveRequest, RejectRequest
from backend.schemas.common import ApprovalStatus
from backend.schemas.envelope import ResponseEnvelope
from hitl.workflow import HITLWorkflow

router = APIRouter(prefix="/v1/hitl", tags=["HITL"])

_workflow = HITLWorkflow()


@router.get("/approvals")
async def list_approvals(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> ResponseEnvelope:
    """GET /v1/hitl/approvals — List approvals."""
    user_id = get_local_user_id()
    filter_status = ApprovalStatus(status) if status else None
    approvals = _workflow.list_approvals(user_id=user_id, status=filter_status, limit=limit)
    return ResponseEnvelope.success(
        data={"approvals": [a.model_dump() for a in approvals], "total": len(approvals)}
    )


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str) -> ResponseEnvelope:
    """GET /v1/hitl/approvals/{approval_id} — Detail."""
    user_id = get_local_user_id()
    approval = _workflow.get_approval(approval_id)
    if not approval:
        return ResponseEnvelope.fail("NOT_FOUND", f"Approval {approval_id} not found")
    if approval.user_id != user_id:
        return ResponseEnvelope.fail("FORBIDDEN", "Approval does not belong to current user")
    return ResponseEnvelope.success(data=approval.model_dump())


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str) -> ResponseEnvelope:
    """POST /v1/hitl/approvals/{approval_id}/approve"""
    try:
        user_id = get_local_user_id()
        approval = _workflow.get_approval(approval_id)
        if approval and approval.user_id != user_id:
            return ResponseEnvelope.fail("FORBIDDEN", "Approval does not belong to current user")
        result = _workflow.approve(approval_id, decided_by=user_id)
        if not result:
            return ResponseEnvelope.fail("NOT_FOUND", "Approval not found")
        return ResponseEnvelope.success(data=result.model_dump())
    except ValueError as e:
        return ResponseEnvelope.fail("INVALID_TRANSITION", str(e))


@router.post("/approvals/{approval_id}/edit-approve")
async def edit_approve(approval_id: str, body: EditApproveRequest) -> ResponseEnvelope:
    """POST /v1/hitl/approvals/{approval_id}/edit-approve"""
    try:
        user_id = get_local_user_id()
        approval = _workflow.get_approval(approval_id)
        if approval and approval.user_id != user_id:
            return ResponseEnvelope.fail("FORBIDDEN", "Approval does not belong to current user")
        result = _workflow.edit_approve(
            approval_id,
            edited_args=body.edited_args,
            decided_by=user_id,
            reason=body.reason,
        )
        if not result:
            return ResponseEnvelope.fail("NOT_FOUND", "Approval not found")
        return ResponseEnvelope.success(data=result.model_dump())
    except ValueError as e:
        return ResponseEnvelope.fail("INVALID_TRANSITION", str(e))


@router.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: RejectRequest) -> ResponseEnvelope:
    """POST /v1/hitl/approvals/{approval_id}/reject"""
    try:
        user_id = get_local_user_id()
        approval = _workflow.get_approval(approval_id)
        if approval and approval.user_id != user_id:
            return ResponseEnvelope.fail("FORBIDDEN", "Approval does not belong to current user")
        result = _workflow.reject(
            approval_id,
            decided_by=user_id,
            reason=body.reason,
        )
        if not result:
            return ResponseEnvelope.fail("NOT_FOUND", "Approval not found")
        return ResponseEnvelope.success(data=result.model_dump())
    except ValueError as e:
        return ResponseEnvelope.fail("INVALID_TRANSITION", str(e))


@router.post("/approvals/{approval_id}/cancel")
async def cancel(approval_id: str) -> ResponseEnvelope:
    """POST /v1/hitl/approvals/{approval_id}/cancel"""
    try:
        user_id = get_local_user_id()
        approval = _workflow.get_approval(approval_id)
        if approval and approval.user_id != user_id:
            return ResponseEnvelope.fail("FORBIDDEN", "Approval does not belong to current user")
        result = _workflow.cancel(approval_id, decided_by=user_id)
        if not result:
            return ResponseEnvelope.fail("NOT_FOUND", "Approval not found")
        return ResponseEnvelope.success(data=result.model_dump())
    except ValueError as e:
        return ResponseEnvelope.fail("INVALID_TRANSITION", str(e))
