"""Common types, enums, and ID generators used across the application."""

from __future__ import annotations

import time
from enum import Enum

from pydantic import BaseModel, Field
from ulid import ULID


# ── Enums ────────────────────────────────────────────────────────


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionStatus(str, Enum):
    PLANNED = "planned"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ── ID Generators ────────────────────────────────────────────────


def generate_id(prefix: str) -> str:
    """Generate a prefixed ULID-based identifier.

    Examples: tsk_01J5..., act_01J5..., apr_01J5..., req_01J5...
    """
    return f"{prefix}_{ULID()}"


def generate_task_id() -> str:
    return generate_id("tsk")


def generate_action_id() -> str:
    return generate_id("act")


def generate_approval_id() -> str:
    return generate_id("apr")


def generate_request_id() -> str:
    return generate_id("req")


# ── Common Models ────────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
