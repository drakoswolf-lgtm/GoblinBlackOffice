from datetime import date

from app.ledgergut.models import (
    BillableStatus,
    PaidBy,
    ReceiptExtraction,
    ReceiptRecord,
    ReimbursementStatus,
)
from app.ledgergut.validation import ValidationPolicy, validate_receipt


def make_record(**overrides: object) -> ReceiptRecord:
    data: dict[str, object] = {
        "submitted_by": "steve",
        "description": "Materials for Jackson Retail patch job",
        "project_name": "Jackson Retail",
        "currency": "CAD",
        "paid_by": PaidBy.STEVE,
        "reimbursement_status": ReimbursementStatus.NOT_REIMBURSED,
        "billable_status": BillableStatus.BILLABLE,
        "assignment_confidence": 0.82,
        "receipt": ReceiptExtraction(
            vendor_name="Home Hardware",
            receipt_date=date(2026, 7, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            currency="CAD",
        ),
        "ocr_confidence": {
            "vendor_name": 0.95,
            "receipt_date": 0.98,
            "total_amount": 0.91,
            "overall": 0.94,
        },
    }
    data.update(overrides)
    return ReceiptRecord(**data)


def test_validate_receipt_returns_no_findings_for_valid_record() -> None:
    record = make_record()

    assert validate_receipt(record, today=date(2026, 7, 14)) == ()


def test_v01_flags_future_receipt_dates() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 20),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            currency="CAD",
        )
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-01"]


def test_v02_flags_stale_receipt_dates_for_black_collar_review() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 3, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            currency="CAD",
        )
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-02"]
    assert findings[0].severity == "warning"


def test_v02_uses_configurable_stale_receipt_window() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 5, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            currency="CAD",
        )
    )

    findings = validate_receipt(
        record,
        today=date(2026, 7, 14),
        policy=ValidationPolicy(default_currency="CAD", stale_receipt_days=30),
    )

    assert [finding.rule_id for finding in findings] == ["V-02"]


def test_v03_flags_non_positive_totals() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 1),
            subtotal="0.00",
            tax_amount="0.00",
            total_amount="0.00",
            currency="CAD",
        )
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-03"]


def test_v04_flags_amount_mismatches_beyond_tolerance() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.20",
            currency="CAD",
        )
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-04"]


def test_v04_allows_tax_rounding_within_tolerance() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.05",
            currency="CAD",
        )
    )

    assert validate_receipt(record, today=date(2026, 7, 14)) == ()


def test_v05_flags_missing_project_assignment() -> None:
    record = make_record(project_name=None, assignment_confidence=None)

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-05"]


def test_v05_allows_manual_project_selection_without_assignment_confidence() -> None:
    record = make_record(assignment_confidence=None)

    assert validate_receipt(record, today=date(2026, 7, 14)) == ()


def test_v05_flags_uncertain_project_assignment() -> None:
    record = make_record(assignment_confidence=0.70)

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-05"]
    assert findings[0].fields == ("project_name", "assignment_confidence")


def test_v06_flags_unknown_payer() -> None:
    record = make_record(paid_by=PaidBy.UNKNOWN)

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-06"]


def test_v07_flags_currency_mismatch() -> None:
    record = make_record(
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 1),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="28.00",
            currency="USD",
        )
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-07"]


def test_v08_flags_missing_invoice_reference_for_already_invoiced_receipts() -> None:
    record = make_record(
        billable_status=BillableStatus.ALREADY_INVOICED,
        invoice_id=None,
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-08"]


def test_v09_flags_each_low_confidence_ocr_field() -> None:
    record = make_record(
        ocr_confidence={
            "vendor_name": 0.74,
            "receipt_date": 0.70,
            "overall": 0.20,
        }
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == ["V-09", "V-09"]
    assert [finding.fields for finding in findings] == [("receipt_date",), ("vendor_name",)]


def test_validate_receipt_can_return_multiple_findings() -> None:
    record = make_record(
        project_name=None,
        paid_by=PaidBy.UNKNOWN,
        billable_status=BillableStatus.ALREADY_INVOICED,
        invoice_id=None,
        ocr_confidence={"vendor_name": 0.70},
        receipt=ReceiptExtraction(
            receipt_date=date(2026, 7, 20),
            subtotal="25.00",
            tax_amount="3.00",
            total_amount="0.00",
            currency="USD",
        ),
    )

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert [finding.rule_id for finding in findings] == [
        "V-01",
        "V-03",
        "V-04",
        "V-05",
        "V-06",
        "V-07",
        "V-08",
        "V-09",
    ]


def test_validation_findings_serialize_deterministically() -> None:
    record = make_record(paid_by=PaidBy.UNKNOWN)

    findings = validate_receipt(record, today=date(2026, 7, 14))

    assert findings[0].to_dict() == {
        "rule_id": "V-06",
        "fields": ["paid_by"],
        "severity": "warning",
        "message": "Payer is unknown and requires review.",
        "requires_human_review": True,
    }
