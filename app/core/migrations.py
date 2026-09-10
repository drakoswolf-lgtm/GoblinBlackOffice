"""Database schema migration entry point for durable Black Office storage."""
from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_database(database_url: str | None = None) -> None:
    """Upgrade the configured database to the current schema head."""
    url = (database_url or os.environ.get("DATABASE_URL", "")).strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required to run database migrations.")

    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
