"""Local-only identity helper.

Provides a stable installation identifier for single-machine deployments.
"""

from __future__ import annotations

import uuid

from backend.config import get_settings


def get_local_user_id() -> str:
    """Return a stable local user ID persisted on disk."""
    settings = get_settings()
    id_file = settings.data_dir / ".installation_id"

    if id_file.exists():
        value = id_file.read_text(encoding="utf-8").strip()
        if value:
            return value

    user_id = f"local-{uuid.uuid4().hex}"
    id_file.write_text(user_id, encoding="utf-8")
    id_file.chmod(0o600)
    return user_id
