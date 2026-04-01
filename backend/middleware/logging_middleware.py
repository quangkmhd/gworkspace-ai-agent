"""Structured JSON logging middleware using structlog."""

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with structured context.

    Captures: method, path, status_code, duration_ms, request_id.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request_error",
                method=request.method,
                path=str(request.url.path),
                request_id=request_id,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_fn = logger.info if response.status_code < 400 else logger.warning
        log_fn(
            "request_completed",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            request_id=request_id,
            duration_ms=duration_ms,
        )
        return response


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON output."""
    import logging

    level = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
            if log_level.upper() == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
