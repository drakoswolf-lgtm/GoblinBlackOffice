"""PostgreSQL-compatible receipt archive for Ledgergut production deployments."""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, create_engine, insert, select

from app.core.migrations import upgrade_database
from app.ledgergut.storage import CSV_FIELDNAMES

metadata = MetaData()
receipts = Table(
    "ledgergut_receipts",
    metadata,
    Column("record_id", String(64), primary_key=True),
    Column("business_id", String(128), nullable=False, index=True),
    Column("saved_at", DateTime(timezone=True), nullable=False),
    Column("payload", Text, nullable=False),
)


class SqlReceiptStore:
    def __init__(self, database_url: str, business_id_provider: Callable[[], str]):
        upgrade_database(database_url)
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self._business_id_provider = business_id_provider
        self._image_dir = Path("runtime") / "ledgergut" / "images"

    def save_receipt(self, record_dict: dict, image_filename: str | None = None) -> str:
        record = dict(record_dict)
        record_id = record.get("record_id") or f"LG-{uuid.uuid4().hex[:8].upper()}"
        saved_at = datetime.now(timezone.utc)
        record["record_id"] = record_id
        record["saved_at"] = saved_at.isoformat()
        if image_filename:
            record["image_filename"] = image_filename
        with self.engine.begin() as connection:
            connection.execute(
                insert(receipts).values(
                    record_id=record_id,
                    business_id=self._business_id_provider(),
                    saved_at=saved_at,
                    payload=json.dumps(record, ensure_ascii=False, separators=(",", ":")),
                )
            )
        return record_id

    def list_receipts(self) -> list[dict]:
        query = (
            select(receipts.c.payload)
            .where(receipts.c.business_id == self._business_id_provider())
            .order_by(receipts.c.saved_at, receipts.c.record_id)
        )
        with self.engine.connect() as connection:
            return [json.loads(payload) for payload in connection.execute(query).scalars().all()]

    def as_csv(self) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for rec in self.list_receipts():
            receipt = rec.get("receipt") or {}
            writer.writerow({
                "record_id": rec.get("record_id", ""),
                "saved_at": rec.get("saved_at", ""),
                "vendor_name": receipt.get("vendor_name", ""),
                "receipt_date": receipt.get("receipt_date", ""),
                "description": rec.get("description", ""),
                "project_name": rec.get("project_name", ""),
                "expense_category": rec.get("expense_category", ""),
                "subtotal": receipt.get("subtotal", ""),
                "tax_amount": receipt.get("tax_amount", ""),
                "total_amount": receipt.get("total_amount", ""),
                "currency": rec.get("currency", ""),
                "paid_by": rec.get("paid_by", ""),
                "reimbursement_status": rec.get("reimbursement_status", ""),
                "billable_status": rec.get("billable_status", ""),
                "invoice_id": rec.get("invoice_id", ""),
                "submitted_by": rec.get("submitted_by", ""),
            })
        return output.getvalue()

    @property
    def image_dir(self) -> Path:
        self._image_dir.mkdir(parents=True, exist_ok=True)
        return self._image_dir
