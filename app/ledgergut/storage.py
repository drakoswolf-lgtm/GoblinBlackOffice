"""JSON-backed receipt storage and CSV export for Ledgergut."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_STORE = Path("runtime") / "ledgergut" / "receipts.json"
_DEFAULT_IMAGE_DIR = Path("runtime") / "ledgergut" / "images"

CSV_FIELDNAMES = [
    "record_id",
    "saved_at",
    "vendor_name",
    "receipt_date",
    "description",
    "project_name",
    "expense_category",
    "subtotal",
    "tax_amount",
    "total_amount",
    "currency",
    "paid_by",
    "reimbursement_status",
    "billable_status",
    "invoice_id",
    "submitted_by",
]


class ReceiptStore:
    """Simple append-only JSON store for receipt records."""

    def __init__(
        self,
        store_path: Path | None = None,
        image_dir: Path | None = None,
    ) -> None:
        self._path = Path(store_path) if store_path else _DEFAULT_STORE
        self._image_dir = Path(image_dir) if image_dir else _DEFAULT_IMAGE_DIR

    def _ensure_paths(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._image_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        self._ensure_paths()
        text = self._path.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = []
        return data if isinstance(data, list) else []

    def _write(self, records: list[dict]) -> None:
        self._ensure_paths()
        self._path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def save_receipt(self, record_dict: dict, image_filename: str | None = None) -> str:
        """Append a record and return its assigned record_id."""
        records = self._load()
        record_dict = dict(record_dict)
        record_id = record_dict.get("record_id") or f"LG-{uuid.uuid4().hex[:8].upper()}"
        record_dict["record_id"] = record_id
        record_dict["saved_at"] = datetime.now(timezone.utc).isoformat()
        if image_filename:
            record_dict["image_filename"] = image_filename
        records.append(record_dict)
        self._write(records)
        return record_id

    def list_receipts(self) -> list[dict]:
        """Return all saved receipts in insertion order."""
        return self._load()

    def as_csv(self) -> str:
        """Return all receipts serialized as a CSV string."""
        records = self._load()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            receipt = rec.get("receipt") or {}
            row = {
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
            }
            writer.writerow(row)
        return output.getvalue()

    @property
    def image_dir(self) -> Path:
        self._ensure_paths()
        return self._image_dir
