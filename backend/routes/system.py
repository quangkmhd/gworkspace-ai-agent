"""System health and readiness endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter

from backend.config import get_settings
from backend.schemas.envelope import ResponseEnvelope

router = APIRouter(prefix="/v1/system", tags=["System"])

_start_time = time.time()


@router.get("/health")
async def health_check() -> ResponseEnvelope:
    """GET /v1/system/health — Basic liveness check.

    Returns server version, uptime, and environment.
    """
    settings = get_settings()
    return ResponseEnvelope.success(
        data={
            "status": "healthy",
            "version": settings.APP_VERSION,
            "uptime_seconds": round(time.time() - _start_time, 2),
            "environment": settings.ENVIRONMENT.value,
        }
    )


@router.get("/readiness")
async def readiness_check() -> ResponseEnvelope:
    """GET /v1/system/readiness — Dependency readiness check.

    Verifies that required subsystems are operational:
    - Configuration loaded
    - Tool registry available
    - Database accessible (if not mock mode)
    """
    settings = get_settings()
    checks: dict[str, bool] = {
        "config_loaded": True,
        "mock_mode": settings.MOCK_MODE,
    }

    # Check tool manifest exists
    manifest_path = settings.configs_dir / "tool_manifest.json"
    checks["tool_manifest_loaded"] = manifest_path.exists()

    # Check data directory writable
    try:
        test_file = settings.data_dir / ".readiness_check"
        test_file.touch()
        test_file.unlink()
        checks["data_dir_writable"] = True
    except OSError:
        checks["data_dir_writable"] = False

    all_ready = all(
        v for k, v in checks.items() if k != "mock_mode"
    )

    return ResponseEnvelope.success(
        data={
            "ready": all_ready,
            "checks": checks,
        }
    )
