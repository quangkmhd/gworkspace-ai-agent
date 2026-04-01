"""Encrypted local token storage using SQLite + Fernet."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import structlog
from cryptography.fernet import Fernet

from backend.config import get_settings

logger = structlog.get_logger("token_store")


class TokenStore:
    """Encrypted token storage backed by SQLite.

    Tokens are encrypted with Fernet before persisting to prevent
    credential leakage if the DB file is compromised.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._db_path = settings.data_dir / "tokens.db"
        self._fernet = self._init_fernet(settings.TOKEN_ENCRYPTION_KEY, settings.data_dir)
        self._init_db()

    @staticmethod
    def _init_fernet(key: str, data_dir: Path) -> Fernet:
        """Initialize Fernet cipher. Auto-generate key if not provided."""
        key_file = data_dir / ".token_key"
        if key:
            return Fernet(key.encode())
        if key_file.exists():
            return Fernet(key_file.read_bytes().strip())
        # Generate and save new key
        new_key = Fernet.generate_key()
        key_file.write_bytes(new_key)
        key_file.chmod(0o600)
        logger.info("token_encryption_key_generated")
        return Fernet(new_key)

    def _init_db(self) -> None:
        """Create tokens table if not exists."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    user_id TEXT PRIMARY KEY,
                    encrypted_data BLOB NOT NULL,
                    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
                )
            """)

    def store(self, user_id: str, token_data: dict[str, Any]) -> None:
        """Encrypt and store token data for a user."""
        encrypted = self._fernet.encrypt(json.dumps(token_data).encode())
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO tokens (user_id, encrypted_data, updated_at)
                   VALUES (?, ?, strftime('%s', 'now'))""",
                (user_id, encrypted),
            )
        logger.info("token_stored", user_id=user_id)

    def get(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve and decrypt token data for a user."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT encrypted_data FROM tokens WHERE user_id = ?", (user_id,)
            ).fetchone()
        if not row:
            return None
        try:
            decrypted = self._fernet.decrypt(row[0])
            return json.loads(decrypted)
        except Exception:
            logger.error("token_decrypt_failed", user_id=user_id)
            return None

    def delete(self, user_id: str) -> bool:
        """Remove token data for a user."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM tokens WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        logger.info("token_deleted", user_id=user_id, deleted=deleted)
        return deleted

    def list_users(self) -> list[str]:
        """List all user IDs with stored tokens."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT user_id FROM tokens").fetchall()
        return [r[0] for r in rows]
