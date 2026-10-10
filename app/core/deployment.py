"""Fail-closed deployment checks for the Black Office beta.

Local development may use the in-memory store and skip login. A production
deployment must explicitly opt into authentication and durable persistence.
The owner-only ephemeral smoke mode is deliberately opt-in and single-worker.
"""
from __future__ import annotations

import os
from collections.abc import Mapping

_TRUE = {"1", "true", "yes"}


def validate_deployment_settings(settings: Mapping[str, str] | None = None) -> None:
    env = os.environ if settings is None else settings
    production = env.get("GBO_ENV", "development").strip().lower() == "production"
    auth_enabled = env.get("GBO_AUTH_REQUIRED", "").strip().lower() in _TRUE
    database_url = env.get("DATABASE_URL", "").strip()
    owner_smoke = env.get("GBO_INTERNAL_SMOKE_TEST", "").strip().lower() in _TRUE

    if production:
        if not auth_enabled:
            raise RuntimeError("Production requires GBO_AUTH_REQUIRED=1; refusing to expose business records.")
        if not env.get("GBO_SECRET", "").strip():
            raise RuntimeError("Production requires a configured GBO_SECRET.")
        if not env.get("GBO_INVITE_TOKEN", "").strip():
            raise RuntimeError("Private beta requires GBO_INVITE_TOKEN.")
        if not database_url and not owner_smoke:
            raise RuntimeError(
                "Production requires DATABASE_URL for durable records. "
                "For an explicitly disposable owner-only test, set GBO_INTERNAL_SMOKE_TEST=1."
            )
        if database_url and not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise RuntimeError("Production DATABASE_URL must use PostgreSQL; local SQLite is not durable.")

    if not database_url:
        raw_workers = env.get("WEB_CONCURRENCY", "1")
        try:
            workers = int(raw_workers)
        except ValueError as exc:
            raise RuntimeError("WEB_CONCURRENCY must be an integer.") from exc
        if workers != 1:
            raise RuntimeError(
                "An in-memory Black Office cannot run with multiple workers: "
                "requests would read different, non-shared records. Set WEB_CONCURRENCY=1 "
                "for disposable local/owner-only tests or configure DATABASE_URL."
            )
