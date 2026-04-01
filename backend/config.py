"""Application configuration using pydantic-settings."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "GWorkspace AI Agent"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # ── Mock Mode ────────────────────────────────────────────────
    # When True, tools return deterministic mock data (no Google credentials needed)
    MOCK_MODE: bool = True

    # ── Google OAuth 2.0 ─────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/v1/auth/google/callback"
    GOOGLE_CREDENTIALS_FILE: str = ""  # Path to credentials.json

    # ── LLM Configuration ────────────────────────────────────────
    LLM_PROVIDER: str = "google"  # google | vertex
    LLM_MODEL: str = "gemini-3-flash-preview"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    GOOGLE_API_KEY: str = ""  # For Google AI Studio (LLM_PROVIDER=google)
    GOOGLE_CLOUD_PROJECT: str = ""  # For Vertex AI (LLM_PROVIDER=vertex)
    GOOGLE_CLOUD_LOCATION: str = "global"  # For Vertex AI (LLM_PROVIDER=vertex)

    # ── Database / Storage ───────────────────────────────────────
    DATABASE_URL: str = "sqlite:///data/gworkspace.db"
    TOKEN_ENCRYPTION_KEY: str = ""  # Fernet key, auto-generated if empty

    # ── HITL Configuration ───────────────────────────────────────
    HITL_APPROVAL_TIMEOUT_SECONDS: int = 3600  # 1 hour default
    HITL_MAX_PENDING_PER_USER: int = 50

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    TOOL_TIMEOUT_SECONDS: int = 30
    TOOL_MAX_RETRIES: int = 3

    # ── Paths ────────────────────────────────────────────────────
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def configs_dir(self) -> Path:
        return self.project_root / "configs"

    @property
    def data_dir(self) -> Path:
        path = self.project_root / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
