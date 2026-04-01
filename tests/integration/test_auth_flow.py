"""Integration tests for auth flow."""

from __future__ import annotations


class TestAuthFlow:
    def test_oauth_start(self, client):
        """Test OAuth start returns auth URL."""
        response = client.get("/v1/auth/google/start")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "auth_url" in data["data"]

    def test_oauth_callback(self, client):
        """Test OAuth callback exchanges code for tokens."""
        response = client.get("/v1/auth/google/callback?code=test_code&state=test_state")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "user_id" in data["data"]

    def test_oauth_scopes(self, client):
        """Test OAuth scopes returns scope list."""
        response = client.get("/v1/auth/google/scopes")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_oauth_connections(self, client):
        """Test OAuth connections returns connection list."""
        response = client.get("/v1/auth/google/connections")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "connections" in data["data"]
