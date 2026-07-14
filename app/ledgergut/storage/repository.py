"""Repository API for persisting Ledgergut records in SQLite."""

from __future__ import annotations

import json
from pathlib import Path
from sqlite3 import Row

from app.ledgergut.models import (
    ReceiptExtraction,
    ReceiptLineItem,
    ReceiptRecord,
    TaxLine,
    ValidationFinding,
)
from app.ledgergut.storage.database import LedgergutDatabase


class SQLiteReceiptRepository:
    """Persists Ledgergut receipt records and findings."""

    def __init__(self, database_path: str | Path) -> None:
        self._database = LedgergutDatabase(database_path)

    def close(self) -> None:
        self._database.close()

    def save_receipt(
        self,
        record: ReceiptRecord,
        findings: tuple[ValidationFinding, ...] = (),
    ) -> ReceiptRecord:
        if not record.record_id:
            raise ValueError("record_id is required to persist a receipt.")

        payload_json = json.dumps(record.to_dict(), sort_keys=True)
        with self._database.connection:
            self._database.connection.execute(
                """
                INSERT INTO receipts (
                    record_id,
                    submitted_by,
                    submitted_at,
                    description,
                    project_name,
                    expense_category,
                    currency,
                    paid_by,
                    reimbursement_status,
                    billable_status,
                    invoice_id,
                    payment_notes,
                    assignment_confidence,
                    needs_user_review,
                    review_notes,
                    status,
                    created_at,
                    receipt_payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                    submitted_by = excluded.submitted_by,
                    submitted_at = excluded.submitted_at,
                    description = excluded.description,
                    project_name = excluded.project_name,
                    expense_category = excluded.expense_category,
                    currency = excluded.currency,
                    paid_by = excluded.paid_by,
                    reimbursement_status = excluded.reimbursement_status,
                    billable_status = excluded.billable_status,
                    invoice_id = excluded.invoice_id,
                    payment_notes = excluded.payment_notes,
                    assignment_confidence = excluded.assignment_confidence,
                    needs_user_review = excluded.needs_user_review,
                    review_notes = excluded.review_notes,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    receipt_payload_json = excluded.receipt_payload_json
                """,
                (
                    record.record_id,
                    record.submitted_by,
                    record.submitted_at.isoformat() if record.submitted_at else None,
                    record.description,
                    record.project_name,
                    record.expense_category,
                    record.currency,
                    record.paid_by.value,
                    record.reimbursement_status.value,
                    record.billable_status.value if record.billable_status else None,
                    record.invoice_id,
                    record.payment_notes,
                    record.assignment_confidence,
                    int(record.needs_user_review),
                    record.review_notes,
                    record.status,
                    record.created_at.isoformat() if record.created_at else None,
                    payload_json,
                ),
            )
            self._database.connection.execute(
                "DELETE FROM validation_findings WHERE receipt_record_id = ?",
                (record.record_id,),
            )
            self._database.connection.executemany(
                """
                INSERT INTO validation_findings (
                    receipt_record_id,
                    rule_id,
                    fields_json,
                    severity,
                    message,
                    requires_human_review
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.record_id,
                        finding.rule_id,
                        json.dumps(list(finding.fields)),
                        finding.severity,
                        finding.message,
                        int(finding.requires_human_review),
                    )
                    for finding in findings
                ],
            )
        return record

    def get_receipt(
        self,
        record_id: str,
    ) -> tuple[ReceiptRecord, tuple[ValidationFinding, ...]] | None:
        row = self._database.connection.execute(
            "SELECT receipt_payload_json FROM receipts WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        record = _record_from_row(row)
        findings = self._get_findings(record_id)
        return record, findings

    def list_receipts(self) -> tuple[ReceiptRecord, ...]:
        rows = self._database.connection.execute(
            "SELECT receipt_payload_json FROM receipts ORDER BY created_at, record_id"
        ).fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def update_receipt(self, record: ReceiptRecord) -> ReceiptRecord:
        if not record.record_id:
            raise ValueError("record_id is required to update a receipt.")
        findings = self._get_findings(record.record_id)
        return self.save_receipt(record, findings=findings)

    def delete_receipt(self, record_id: str) -> None:
        with self._database.connection:
            self._database.connection.execute(
                "DELETE FROM receipts WHERE record_id = ?",
                (record_id,),
            )

    def _get_findings(self, record_id: str) -> tuple[ValidationFinding, ...]:
        rows = self._database.connection.execute(
            """
            SELECT rule_id, fields_json, severity, message, requires_human_review
            FROM validation_findings
            WHERE receipt_record_id = ?
            ORDER BY id ASC
            """,
            (record_id,),
        ).fetchall()
        return tuple(
            ValidationFinding(
                rule_id=row["rule_id"],
                fields=tuple(json.loads(row["fields_json"])),
                severity=row["severity"],
                message=row["message"],
                requires_human_review=bool(row["requires_human_review"]),
            )
            for row in rows
        )


def _record_from_row(row: Row) -> ReceiptRecord:
    payload = json.loads(row["receipt_payload_json"])
    receipt_payload = payload["receipt"]
    return ReceiptRecord(
        record_id=payload.get("record_id"),
        collar_id=payload.get("collar_id", "black_collar"),
        submitted_by=payload["submitted_by"],
        submitted_at=payload.get("submitted_at"),
        description=payload["description"],
        project_name=payload.get("project_name"),
        expense_category=payload.get("expense_category"),
        currency=payload.get("currency"),
        paid_by=payload.get("paid_by", "unknown"),
        reimbursement_status=payload.get("reimbursement_status", "unknown"),
        billable_status=payload.get("billable_status"),
        invoice_id=payload.get("invoice_id"),
        payment_notes=payload.get("payment_notes"),
        assignment_confidence=payload.get("assignment_confidence"),
        receipt=_receipt_from_payload(receipt_payload),
        ocr_confidence=payload.get("ocr_confidence", {}),
        needs_user_review=bool(payload.get("needs_user_review", False)),
        review_notes=payload.get("review_notes"),
        status=payload.get("status", "pending_review"),
        created_at=payload.get("created_at"),
    )


def _receipt_from_payload(payload: dict[str, object]) -> ReceiptExtraction:
    return ReceiptExtraction(
        vendor_name=payload.get("vendor_name"),
        receipt_date=payload.get("receipt_date"),
        line_items=tuple(
            ReceiptLineItem(
                name=line_item["name"],
                quantity=line_item["quantity"],
                unit_price=line_item["unit_price"],
            )
            for line_item in payload.get("line_items", [])
        ),
        subtotal=payload.get("subtotal"),
        tax_lines=tuple(
            TaxLine(label=tax_line["label"], amount=tax_line["amount"])
            for tax_line in payload.get("tax_lines", [])
        ),
        tax_amount=payload.get("tax_amount"),
        total_amount=payload.get("total_amount"),
        payment_method=payload.get("payment_method"),
        receipt_number=payload.get("receipt_number"),
        currency=payload.get("currency"),
    )
