"""Unified response envelope for all API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.common import generate_request_id


class Meta(BaseModel):
    """Response metadata."""

    request_id: str = Field(default_factory=generate_request_id)


class ResponseEnvelope(BaseModel):
    """Standard API response wrapper.

    All endpoints return this shape:
    {
        "ok": true/false,
        "data": { ... } | null,
        "error": { "code": "...", "message": "..." } | null,
        "meta": { "request_id": "req_..." }
    }
    """

    ok: bool
    data: Any = None
    error: dict[str, Any] | None = None
    meta: Meta = Field(default_factory=Meta)

    @classmethod
    def success(cls, data: Any = None, request_id: str | None = None) -> ResponseEnvelope:
        """Create a successful response."""
        meta = Meta(request_id=request_id) if request_id else Meta()
        return cls(ok=True, data=data, meta=meta)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: Any = None,
        request_id: str | None = None,
    ) -> ResponseEnvelope:
        """Create a failure response."""
        meta = Meta(request_id=request_id) if request_id else Meta()
        error = {"code": code, "message": message}
        if details:
            error["details"] = details
        return cls(ok=False, error=error, meta=meta)
