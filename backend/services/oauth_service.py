"""Google OAuth 2.0 service — handles authorization flow, token exchange, refresh, revoke."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from backend.config import get_settings

logger = structlog.get_logger("oauth")

# Default scopes (least privilege for MVP)
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class OAuthService:
    """Manages Google OAuth 2.0 flows."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _get_client_config(self) -> dict[str, Any]:
        """Load OAuth client config from credentials file or env vars."""
        cred_file = self._settings.GOOGLE_CREDENTIALS_FILE
        if cred_file and Path(cred_file).exists():
            with open(cred_file) as f:
                return json.load(f)

        # Build from env vars
        return {
            "web": {
                "client_id": self._settings.GOOGLE_CLIENT_ID,
                "client_secret": self._settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [self._settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def create_authorization_url(self, scopes: list[str] | None = None) -> tuple[str, str]:
        """Generate Google OAuth consent URL.

        Returns (auth_url, state) tuple.
        """
        if self._settings.MOCK_MODE:
            return ("http://localhost:8000/v1/auth/google/callback?code=mock_code&state=mock", "mock")

        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=scopes or DEFAULT_SCOPES,
            redirect_uri=self._settings.GOOGLE_REDIRECT_URI,
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        logger.info("oauth_url_created", state=state)
        return auth_url, state

    def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Returns dict with access_token, refresh_token, expiry, scopes.
        """
        if self._settings.MOCK_MODE:
            return {
                "access_token": "mock_access_token_" + code[:8],
                "refresh_token": "mock_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "expiry": "2099-12-31T23:59:59Z",
                "scopes": DEFAULT_SCOPES,
            }

        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=DEFAULT_SCOPES,
            redirect_uri=self._settings.GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_data = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
            "scopes": list(creds.scopes) if creds.scopes else DEFAULT_SCOPES,
        }
        logger.info("oauth_code_exchanged")
        return token_data

    def refresh_token(self, token_data: dict[str, Any]) -> dict[str, Any]:
        """Refresh an expired access token."""
        if self._settings.MOCK_MODE:
            return {**token_data, "access_token": "mock_refreshed_token"}

        from google.auth.transport.requests import Request

        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", self._settings.GOOGLE_CLIENT_ID),
            client_secret=token_data.get("client_secret", self._settings.GOOGLE_CLIENT_SECRET),
        )
        creds.refresh(Request())

        token_data["access_token"] = creds.token
        if creds.expiry:
            token_data["expiry"] = creds.expiry.isoformat()
        logger.info("oauth_token_refreshed")
        return token_data

    def revoke_token(self, token_data: dict[str, Any]) -> bool:
        """Revoke tokens at Google."""
        if self._settings.MOCK_MODE:
            logger.info("oauth_token_revoked_mock")
            return True

        import httpx

        resp = httpx.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token_data.get("access_token")},
        )
        success = resp.status_code == 200
        logger.info("oauth_token_revoked", success=success)
        return success

    def get_credentials(self, token_data: dict[str, Any]) -> Credentials:
        """Build google.oauth2 Credentials from stored token data."""
        return Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", self._settings.GOOGLE_CLIENT_ID),
            client_secret=token_data.get("client_secret", self._settings.GOOGLE_CLIENT_SECRET),
            scopes=token_data.get("scopes", DEFAULT_SCOPES),
        )
