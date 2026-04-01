"""Request ID middleware — generates and attaches X-Request-ID to every request."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.schemas.common import generate_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response cycle.

    - If client sends X-Request-ID, reuse it.
    - Otherwise generate a new req_... ID.
    - ID is stored in request.state.request_id for downstream use.
    - ID is returned in X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
