"""Shared fixtures for all tests."""

from __future__ import annotations

import os

# Force mock mode for all tests
os.environ["MOCK_MODE"] = "true"
os.environ["API_KEY_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///data/test_gworkspace.db"

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings, Settings
from backend.main import create_app
from tools.registry import ToolRegistry


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset cached settings between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    """Create a fresh FastAPI app for testing."""
    ToolRegistry.reset()
    return create_app()


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture
def tool_registry():
    """Get a fresh tool registry."""
    ToolRegistry.reset()
    return ToolRegistry.get()
