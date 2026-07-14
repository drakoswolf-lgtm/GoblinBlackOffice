"""Ledgergut receipt validation rules V-01 through V-09."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from datetime import timedelta

from app.ledgergut.models import BillableStatus, PaidBy, ReceiptRecord, ValidationFinding

BLACK_COLLAR_DEFAULT_CURRENCY = "CAD"
CONFIDENCE_THRESHOLD = 0.75
TOTAL_TOLERANCE = Decimal("0.05")


@dataclass(frozen=True)
class ValidationPolicy:
    """Configurable validation settings for a Ledgergut receipt workflow."""

    default_currency: str | None = None
    stale_receipt_days: int | None = None
    assignment_confidence_threshold: float = CONFIDENCE_THRESHOLD
    ocr_confidence_threshold: float = CONFIDENCE_THRESHOLD


BLACK_COLLAR_VALIDATION_POLICY = ValidationPolicy(
    default_currency=BLACK_COLLAR_DEFAULT_CURRENCY,
    stale_receipt_days=90,
)


def validate_receipt(
    record: ReceiptRecord,
    *,
    today: date | None = None,
    policy: ValidationPolicy | None = None,
) -> tuple[ValidationFinding, ...]:
    """Return deterministic structured validation findings for a receipt record."""

    findings: list[ValidationFinding] = []
    evaluation_date = today or datetime.now(timezone.utc).date()
    receipt = record.receipt
    validation_policy = policy or (
        BLACK_COLLAR_VALIDATION_POLICY
        if record.collar_id == "black_collar"
        else ValidationPolicy()
    )

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

    if (
        record.collar_id == "black_collar"
        and validation_policy.stale_receipt_days is not None
        and receipt.receipt_date is not None
        and receipt.receipt_date
        < evaluation_date - timedelta(days=validation_policy.stale_receipt_days)
    ):
        findings.append(
            ValidationFinding(
                rule_id="V-02",
                fields=("receipt_date",),
                severity="warning",
                message=(
                    "Receipt date is older than the configured stale-receipt review "
                    f"window ({validation_policy.stale_receipt_days} days)."
                ),
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
        bool(record.project_name)
        and record.assignment_confidence is not None
        and record.assignment_confidence
        < validation_policy.assignment_confidence_threshold
    )
    if record.collar_id == "black_collar" and (project_missing or project_uncertain):
        fields = ("project_name",) if project_missing else ("project_name", "assignment_confidence")
        message = (
            "Project assignment is missing and requires review."
            if project_missing
            else (
                "Inferred project assignment confidence is below "
                f"{validation_policy.assignment_confidence_threshold:.2f}."
            )
        )
        findings.append(
            ValidationFinding(
                rule_id="V-05",
                fields=fields,
                severity="warning",
                message=message,
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
        validation_policy.default_currency if record.collar_id == "black_collar" else None
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
        if (
            field_name == "overall"
            or score is None
            or score >= validation_policy.ocr_confidence_threshold
        ):
            continue
        findings.append(
            ValidationFinding(
                rule_id="V-09",
                fields=(field_name,),
                severity="warning",
                message=(
                    f"OCR confidence for '{field_name}' is below "
                    f"{validation_policy.ocr_confidence_threshold:.2f}."
                ),
                requires_human_review=True,
            )
        )

    return tuple(findings)
