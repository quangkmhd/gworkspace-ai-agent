"""Idempotency-Key middleware for write/send/delete operations."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Prevent duplicate execution of write operations.

    - Checks Idempotency-Key header on POST/PUT/PATCH/DELETE requests.
    - If the same key was seen before, returns the cached response.
    - Stores key -> response in an in-memory dict (replace with Redis/DB for prod).
    """

    def __init__(self, app: Any, ttl_seconds: int = 3600) -> None:
        super().__init__(app)
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only apply to mutation methods
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # Create cache key from method + path + idempotency key
        cache_key = hashlib.sha256(
            f"{request.method}:{request.url.path}:{idempotency_key}".encode()
        ).hexdigest()

        # Check cache
        now = time.time()
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self._ttl:
                return JSONResponse(
                    content=entry["body"],
                    status_code=entry["status_code"],
                    headers={"X-Idempotent-Replayed": "true"},
                )
            else:
                del self._cache[cache_key]

        # Execute and cache
        response = await call_next(request)

        # Only cache successful responses
        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body += chunk.encode()
                else:
                    body += chunk

            try:
                body_json = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                body_json = {"raw": body.decode("utf-8", errors="replace")}

            self._cache[cache_key] = {
                "body": body_json,
                "status_code": response.status_code,
                "timestamp": now,
            }

            # Cleanup old entries periodically
            if len(self._cache) > 1000:
                expired_keys = [
                    k for k, v in self._cache.items() if now - v["timestamp"] > self._ttl
                ]
                for k in expired_keys:
                    del self._cache[k]

            return JSONResponse(
                content=body_json,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        return response
