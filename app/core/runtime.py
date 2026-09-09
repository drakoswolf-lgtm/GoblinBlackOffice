"""Process-local shared Black Office runtime store.

This keeps all live specialists on one Office record set until PostgreSQL
replaces the in-memory implementation.
"""

from __future__ import annotations

import os

from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Business

business_id = os.environ.get("GBO_BUSINESS_ID", "local-development")
office_store = InMemoryBlackOfficeStore.create()
office_store.businesses.save(
    Business(
        business_id=business_id,
        name=os.environ.get("GBO_BUSINESS_NAME", "Local Black Office"),
    )
)
