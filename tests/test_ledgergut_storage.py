from __future__ import annotations

import sqlite3
from pathlib import Path

from app.ledgergut.models import (
    ReceiptExtraction,
    ReceiptRecord,
    ValidationFinding,
)
from app.ledgergut.storage.repository import SQLiteReceiptRepository


def make_record(record_id: str, **overrides: object) -> ReceiptRecord:
    data: dict[str, object] = {
        "record_id": record_id,
        "submitted_by": "steve",
        "description": f"Receipt {record_id}",
        "project_name": "Jackson Retail",
        "currency": "CAD",
        "paid_by": "steve",
        "reimbursement_status": "not_reimbursed",
        "billable_status": "billable",
        "assignment_confidence": 0.88,
        "receipt": ReceiptExtraction(
            vendor_name="Home Hardware",
            receipt_date="2026-07-01",
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            payment_method="Visa ...1234",
            receipt_number=f"RCT-{record_id}",
            currency="CAD",
        ),
        "ocr_confidence": {"overall": 0.92, "vendor_name": 0.91},
        "status": "pending_review",
        "created_at": "2026-07-14T10:00:00+00:00",
    }
    data.update(overrides)
    return ReceiptRecord(**data)


def make_findings() -> tuple[ValidationFinding, ...]:
    return (
        ValidationFinding(
            rule_id="V-06",
            fields=("paid_by",),
            severity="warning",
            message="Payer is unknown and requires review.",
            requires_human_review=True,
        ),
        ValidationFinding(
            rule_id="V-08",
            fields=("billable_status", "invoice_id"),
            severity="warning",
            message="Already invoiced receipts must include an invoice reference.",
            requires_human_review=True,
        ),
    )


def test_database_initialization_on_first_run(tmp_path: Path) -> None:
    db_path = tmp_path / "ledgergut.db"

    repository = SQLiteReceiptRepository(db_path)
    repository.close()

    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "receipts" in tables
    assert "validation_findings" in tables


def test_empty_database_behavior(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")

    assert repository.list_receipts() == ()
    assert repository.get_receipt("does-not-exist") is None

    repository.close()


def test_save_and_retrieve_receipt_round_trip(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    record = make_record("LG-001")
    findings = make_findings()

    repository.save_receipt(record, findings)
    persisted = repository.get_receipt("LG-001")

    assert persisted is not None
    loaded_record, loaded_findings = persisted
    assert loaded_record == record
    assert loaded_findings == findings

    repository.close()


def test_saves_validation_findings(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    record = make_record("LG-002")
    findings = make_findings()

    repository.save_receipt(record, findings)
    persisted = repository.get_receipt("LG-002")

    assert persisted is not None
    _, loaded_findings = persisted
    assert [finding.rule_id for finding in loaded_findings] == ["V-06", "V-08"]
    assert loaded_findings[1].fields == ("billable_status", "invoice_id")

    repository.close()


def test_update_receipt_status(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    record = make_record("LG-003")
    repository.save_receipt(record, make_findings())

    updated = make_record(
        "LG-003",
        status="approved",
        needs_user_review=False,
        review_notes="Approved by reviewer",
    )
    repository.update_receipt(updated)
    persisted = repository.get_receipt("LG-003")

    assert persisted is not None
    loaded_record, loaded_findings = persisted
    assert loaded_record.status == "approved"
    assert loaded_record.review_notes == "Approved by reviewer"
    assert len(loaded_findings) == 2

    repository.close()


def test_list_receipts(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    first = make_record("LG-010", created_at="2026-07-14T10:00:00+00:00")
    second = make_record("LG-020", created_at="2026-07-14T11:00:00+00:00")

    repository.save_receipt(first, ())
    repository.save_receipt(second, ())

    receipts = repository.list_receipts()

    assert [record.record_id for record in receipts] == ["LG-010", "LG-020"]
    repository.close()


def test_delete_receipt(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    repository.save_receipt(make_record("LG-999"), make_findings())

    repository.delete_receipt("LG-999")

    assert repository.get_receipt("LG-999") is None
    assert repository.list_receipts() == ()
    repository.close()


def test_multiple_receipts(tmp_path: Path) -> None:
    repository = SQLiteReceiptRepository(tmp_path / "ledgergut.db")
    repository.save_receipt(make_record("LG-101"), ())
    repository.save_receipt(make_record("LG-102"), ())
    repository.save_receipt(make_record("LG-103"), ())

    ids = [record.record_id for record in repository.list_receipts()]

    assert ids == ["LG-101", "LG-102", "LG-103"]
    repository.close()
