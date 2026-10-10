"""Shared Black Office runtime persistence selection.

DATABASE_URL opts the application into durable SQL storage. Without it, tests
and local development retain the zero-setup in-memory store.
"""

from __future__ import annotations

import os

from app.core.deployment import validate_deployment_settings
from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Business
from app.core.sql_store import SqlBlackOfficeStore

# Guard production access and worker topology before any store is opened.
validate_deployment_settings()

business_id = os.environ.get("GBO_BUSINESS_ID", "local-development")
database_url = os.environ.get("DATABASE_URL", "").strip()
office_store = SqlBlackOfficeStore(database_url) if database_url else InMemoryBlackOfficeStore.create()

if office_store.businesses.get(business_id, business_id) is None:
    office_store.businesses.save(
        Business(
            business_id=business_id,
            name=os.environ.get("GBO_BUSINESS_NAME", "Local Black Office"),
        )
    )
