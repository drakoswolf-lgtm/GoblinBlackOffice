"""Ledgergut receipt validation rules V-01 through V-09."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.ledgergut.models import BillableStatus, PaidBy, ReceiptRecord, ValidationFinding

BLACK_COLLAR_DEFAULT_CURRENCY = "CAD"
CONFIDENCE_THRESHOLD = 0.75
TOTAL_TOLERANCE = Decimal("0.05")


def validate_receipt(
    record: ReceiptRecord,
    *,
    today: date | None = None,
) -> tuple[ValidationFinding, ...]:
    """Return deterministic structured validation findings for a receipt record."""

    findings: list[ValidationFinding] = []
    evaluation_date = today or datetime.now(timezone.utc).date()
    receipt = record.receipt

    if receipt.receipt_date and receipt.receipt_date > evaluation_date:
        findings.append(
            ValidationFinding(
                rule_id="V-01",
                fields=("receipt_date",),
                severity="error",
                message="Receipt date cannot be in the future.",
                requires_human_review=True,
            )
        )

    if receipt.total_amount is not None and receipt.total_amount <= Decimal("0"):
        findings.append(
            ValidationFinding(
                rule_id="V-03",
                fields=("total_amount",),
                severity="error",
                message="Total amount must be greater than zero.",
                requires_human_review=True,
            )
        )

    if (
        receipt.subtotal is not None
        and receipt.tax_amount is not None
        and receipt.total_amount is not None
        and abs((receipt.subtotal + receipt.tax_amount) - receipt.total_amount) > TOTAL_TOLERANCE
    ):
        findings.append(
            ValidationFinding(
                rule_id="V-04",
                fields=("subtotal", "tax_amount", "total_amount"),
                severity="warning",
                message="Subtotal plus tax does not match total within ±0.05.",
                requires_human_review=True,
            )
        )

    project_missing = not record.project_name
    project_uncertain = (
        record.assignment_confidence is None
        or record.assignment_confidence < CONFIDENCE_THRESHOLD
    )
    if record.collar_id == "black_collar" and (project_missing or project_uncertain):
        detail = "missing" if project_missing else "uncertain"
        findings.append(
            ValidationFinding(
                rule_id="V-05",
                fields=("project_name", "assignment_confidence"),
                severity="warning",
                message=f"Project assignment is {detail} and requires review.",
                requires_human_review=True,
            )
        )

    if record.paid_by == PaidBy.UNKNOWN:
        findings.append(
            ValidationFinding(
                rule_id="V-06",
                fields=("paid_by",),
                severity="warning",
                message="Payer is unknown and requires review.",
                requires_human_review=True,
            )
        )

    expected_currency = record.currency or (
        BLACK_COLLAR_DEFAULT_CURRENCY if record.collar_id == "black_collar" else None
    )
    detected_currency = receipt.currency
    if expected_currency and detected_currency:
        if expected_currency.upper() != detected_currency.upper():
            findings.append(
                ValidationFinding(
                    rule_id="V-07",
                    fields=("currency", "receipt.currency"),
                    severity="warning",
                    message=(
                        f"Detected currency '{detected_currency}' does not match "
                        f"expected currency '{expected_currency}'."
                    ),
                    requires_human_review=True,
                )
            )

    if (
        record.billable_status == BillableStatus.ALREADY_INVOICED
        and not record.invoice_id
    ):
        findings.append(
            ValidationFinding(
                rule_id="V-08",
                fields=("billable_status", "invoice_id"),
                severity="warning",
                message="Already invoiced receipts must include an invoice reference.",
                requires_human_review=True,
            )
        )

    for field_name, score in sorted(record.ocr_confidence.items()):
        if field_name == "overall" or score is None or score >= CONFIDENCE_THRESHOLD:
            continue
        findings.append(
            ValidationFinding(
                rule_id="V-09",
                fields=(field_name,),
                severity="warning",
                message=(
                    f"OCR confidence for '{field_name}' is below "
                    f"{CONFIDENCE_THRESHOLD:.2f}."
                ),
                requires_human_review=True,
            )
        )

    return tuple(findings)
