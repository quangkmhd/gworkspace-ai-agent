"""OAuth & Workspace Connection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from backend.middleware.auth import CurrentUser
from backend.schemas.envelope import ResponseEnvelope
from backend.services.oauth_service import OAuthService
from backend.services.token_store import TokenStore

router = APIRouter(prefix="/v1/auth/google", tags=["Auth"])


def _oauth() -> OAuthService:
    return OAuthService()


def _store() -> TokenStore:
    return TokenStore()


@router.get("/start")
async def oauth_start() -> ResponseEnvelope:
    """GET /v1/auth/google/start — Redirect URL for Google OAuth consent."""
    auth_url, state = _oauth().create_authorization_url()
    return ResponseEnvelope.success(data={"auth_url": auth_url, "state": state})


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
) -> ResponseEnvelope:
    """GET /v1/auth/google/callback — Exchange authorization code for tokens."""
    token_data = _oauth().exchange_code(code)
    # In MVP use state or a default user_id
    user_id = f"user_{state[:8]}" if state else "user_default"
    _store().store(user_id, token_data)
    return ResponseEnvelope.success(
        data={
            "user_id": user_id,
            "scopes": token_data.get("scopes", []),
            "message": "OAuth connection established",
        }
    )


@router.post("/refresh")
async def oauth_refresh(user: CurrentUser) -> ResponseEnvelope:
    """POST /v1/auth/google/refresh — Refresh access token."""
    user_id = user or "user_default"
    store = _store()
    token_data = store.get(user_id)
    if not token_data:
        return ResponseEnvelope.fail("NO_TOKEN", "No token found for user")

    refreshed = _oauth().refresh_token(token_data)
    store.store(user_id, refreshed)
    return ResponseEnvelope.success(data={"message": "Token refreshed"})


@router.post("/revoke")
async def oauth_revoke(user: CurrentUser) -> ResponseEnvelope:
    """POST /v1/auth/google/revoke — Revoke tokens and delete stored data."""
    user_id = user or "user_default"
    store = _store()
    token_data = store.get(user_id)
    if token_data:
        _oauth().revoke_token(token_data)
    store.delete(user_id)
    return ResponseEnvelope.success(data={"message": "Token revoked"})


@router.get("/scopes")
async def oauth_scopes(user: CurrentUser) -> ResponseEnvelope:
    """GET /v1/auth/google/scopes — List granted scopes for current user."""
    user_id = user or "user_default"
    token_data = _store().get(user_id)
    scopes = token_data.get("scopes", []) if token_data else []
    return ResponseEnvelope.success(data={"scopes": scopes})


@router.get("/connections")
async def oauth_connections() -> ResponseEnvelope:
    """GET /v1/auth/google/connections — List all active OAuth connections."""
    users = _store().list_users()
    return ResponseEnvelope.success(
        data={"connections": [{"user_id": u, "status": "active"} for u in users]}
    )
