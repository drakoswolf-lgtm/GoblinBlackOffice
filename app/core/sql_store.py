"""Durable SQL persistence for shared Black Office records.

Production is expected to use PostgreSQL via DATABASE_URL. SQLite remains useful
for local/test verification of repository semantics without provisioning a
service.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from typing import Generic, TypeVar, get_type_hints

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, create_engine, delete, insert, select
from sqlalchemy.engine import Engine

from app.core.models import Agreement, Business, Client, Expense, Invoice, Payment, Project
from app.core.storage import BlackOfficeStore

T = TypeVar("T")

metadata = MetaData()
records = Table(
    "office_records",
    metadata,
    Column("record_type", String(32), primary_key=True),
    Column("record_id", String(128), primary_key=True),
    Column("business_id", String(128), nullable=False, index=True),
    Column("payload", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


def _json_default(value):
    if isinstance(value, Decimal):
        return {"__decimal__": str(value)}
    if isinstance(value, (date, datetime)):
        return {"__date__": value.isoformat()}
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Unsupported value {value!r}")


def _json_hook(value):
    if "__decimal__" in value:
        return Decimal(value["__decimal__"])
    if "__date__" in value:
        text = value["__date__"]
        return datetime.fromisoformat(text) if "T" in text else date.fromisoformat(text)
    return value


class SqlRepository(Generic[T]):
    def __init__(self, engine: Engine, model_type: type[T], id_field: str):
        self.engine = engine
        self.model_type = model_type
        self.id_field = id_field
        self.record_type = model_type.__name__.lower()
        self.type_hints = get_type_hints(model_type)

    def save(self, record: T) -> T:
        payload = json.dumps(asdict(record), default=_json_default, separators=(",", ":"))
        record_id = str(getattr(record, self.id_field))
        business_id = str(getattr(record, "business_id"))
        now = datetime.utcnow()
        with self.engine.begin() as connection:
            connection.execute(
                delete(records).where(
                    records.c.record_type == self.record_type,
                    records.c.record_id == record_id,
                    records.c.business_id == business_id,
                )
            )
            connection.execute(
                insert(records).values(
                    record_type=self.record_type,
                    record_id=record_id,
                    business_id=business_id,
                    payload=payload,
                    created_at=now,
                    updated_at=now,
                )
            )
        return record

    def get(self, record_id: str, business_id: str | None = None) -> T | None:
        query = select(records.c.payload).where(
            records.c.record_type == self.record_type,
            records.c.record_id == record_id,
        )
        if business_id is not None:
            query = query.where(records.c.business_id == business_id)
        with self.engine.connect() as connection:
            payloads = connection.execute(query).scalars().all()
        if not payloads:
            return None
        if len(payloads) > 1:
            raise LookupError("Record ID is ambiguous across businesses; supply business_id.")
        return self._decode(payloads[0])

    def list_for_business(self, business_id: str) -> list[T]:
        query = select(records.c.payload).where(
            records.c.record_type == self.record_type,
            records.c.business_id == business_id,
        ).order_by(records.c.created_at, records.c.record_id)
        with self.engine.connect() as connection:
            payloads = connection.execute(query).scalars().all()
        return [self._decode(payload) for payload in payloads]

    def _decode(self, payload: str) -> T:
        data = json.loads(payload, object_hook=_json_hook)
        for name, annotation in self.type_hints.items():
            value = data.get(name)
            if isinstance(value, str) and isinstance(annotation, type) and issubclass(annotation, Enum):
                data[name] = annotation(value)
        return self.model_type(**data)


class SqlBlackOfficeStore(BlackOfficeStore):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        metadata.create_all(self.engine)
        self.businesses = SqlRepository(self.engine, Business, "business_id")
        self.clients = SqlRepository(self.engine, Client, "client_id")
        self.projects = SqlRepository(self.engine, Project, "project_id")
        self.agreements = SqlRepository(self.engine, Agreement, "agreement_id")
        self.expenses = SqlRepository(self.engine, Expense, "expense_id")
        self.invoices = SqlRepository(self.engine, Invoice, "invoice_id")
        self.payments = SqlRepository(self.engine, Payment, "payment_id")
