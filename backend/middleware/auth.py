"""Bearer token authentication middleware.

For local dev: simple API key check (optional).
For Google Workspace: separate OAuth flow in backend/services/oauth_service.py.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import get_settings

security_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(security_scheme)
    ] = None,
) -> str | None:
    """Verify the Bearer token if API key auth is enabled.

    Returns the token/user identifier if valid, None if auth is disabled.
    """
    settings = get_settings()

    if not settings.API_KEY_ENABLED:
        return "anonymous"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


# Type alias for dependency injection
CurrentUser = Annotated[str | None, Depends(verify_api_key)]
