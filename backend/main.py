"""FastAPI application entry point.

Creates the app, registers middleware & routes, configures logging.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.middleware.idempotency import IdempotencyMiddleware
from backend.middleware.logging_middleware import LoggingMiddleware, configure_logging
from backend.middleware.request_id import RequestIdMiddleware

logger = structlog.get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifecycle — startup and shutdown hooks."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    logger.info(
        "app_starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT.value,
        mock_mode=settings.MOCK_MODE,
    )

    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    yield

    logger.info("app_shutting_down")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI Agent for Google Workspace with Human-in-the-Loop approval. "
            "Provides tool orchestration, risk-based approval gates, and audit logging."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware (order matters: outermost first) ───────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # ── Register Routes ──────────────────────────────────────────
    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API route modules."""
    from backend.routes.system import router as system_router

    app.include_router(system_router)

    # Phase B: Auth
    from backend.routes.auth import router as auth_router

    app.include_router(auth_router)

    # Phase C: Tools + Workspace
    from backend.routes.tools import router as tools_router

    app.include_router(tools_router)

    from backend.routes.workspace.gmail import router as gmail_router
    from backend.routes.workspace.calendar import router as calendar_router
    from backend.routes.workspace.docs import router as docs_router
    from backend.routes.workspace.sheets import router as sheets_router
    from backend.routes.workspace.drive import router as drive_router

    app.include_router(gmail_router)
    app.include_router(calendar_router)
    app.include_router(docs_router)
    app.include_router(sheets_router)
    app.include_router(drive_router)

    # Phase D: Agent
    from backend.routes.agent import router as agent_router

    app.include_router(agent_router)

    # Phase E: HITL + Audit
    from backend.routes.hitl import router as hitl_router

    app.include_router(hitl_router)

    from backend.routes.audit import router as audit_router

    app.include_router(audit_router)


# Module-level app instance for uvicorn
app = create_app()
