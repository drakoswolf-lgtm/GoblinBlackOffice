import json
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.ledgergut.models import (
    BillableStatus,
    PaidBy,
    ReceiptExtraction,
    ReceiptLineItem,
    ReceiptRecord,
    ReimbursementStatus,
    TaxLine,
)


def test_receipt_record_serializes_enums_and_nested_models() -> None:
    record = ReceiptRecord(
        record_id="LG-20260703-0042",
        submitted_by="steve",
        description="Materials for Jackson Retail patch job",
        project_name="Jackson Retail",
        currency="CAD",
        paid_by=PaidBy.STEVE,
        reimbursement_status=ReimbursementStatus.NOT_REIMBURSED,
        billable_status=BillableStatus.MAYBE_BILLABLE,
        assignment_confidence=0.82,
        receipt=ReceiptExtraction(
            vendor_name="Home Hardware",
            receipt_date="2026-07-01",
            line_items=(ReceiptLineItem(name="Fasteners", quantity=2, unit_price="12.50"),),
            subtotal="25.00",
            tax_lines=(
                TaxLine(label="GST", amount="1.25"),
                TaxLine(label="PST", amount="1.75"),
            ),
            tax_amount="3.00",
            total_amount="28.00",
            payment_method="Visa ...1234",
            receipt_number="RCT-00421",
            currency="CAD",
        ),
        ocr_confidence={"vendor_name": 0.95, "receipt_date": 0.98, "overall": 0.94},
    )

    payload = record.to_dict()

    assert payload["paid_by"] == "steve"
    assert payload["reimbursement_status"] == "not_reimbursed"
    assert payload["billable_status"] == "maybe_billable"
    assert payload["receipt"]["line_items"][0]["unit_price"] == 12.5
    assert payload["receipt"]["tax_lines"][1]["label"] == "PST"
    json.dumps(payload)


def test_receipt_models_are_immutable() -> None:
    record = ReceiptRecord(
        submitted_by="steve",
        description="Immutable test",
        receipt=ReceiptExtraction(receipt_date=date(2026, 7, 1), total_amount="1.00"),
    )

    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        record.description = "Changed"  # type: ignore[misc]


def test_receipt_record_rejects_unparseable_dates() -> None:
    with pytest.raises(ValueError, match="receipt_date must be an ISO-8601 date"):
        ReceiptExtraction(receipt_date="07/01/2026")
