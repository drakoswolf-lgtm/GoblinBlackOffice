"""Typed Ledgergut receipt domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Mapping


def _coerce_decimal(value: Decimal | int | float | str | None, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal value.") from exc


def _coerce_date(value: date | str | None, field_name: str) -> date | None:
    if value is None or isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 date.") from exc


def _coerce_datetime(value: datetime | str | None, field_name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime.") from exc


def _coerce_confidence(value: float | int | str | None, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a numeric confidence score.") from exc
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
    return confidence


def _serialize_decimal(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


class PaidBy(str, Enum):
    """Canonical Ledgergut payer values."""

    STEVE = "steve"
    COMPANY_CARD = "company_card"
    CLIENT_CARD = "client_card"
    ROB_VISA = "rob_visa"
    CASH = "cash"
    UNKNOWN = "unknown"


class ReimbursementStatus(str, Enum):
    """Canonical Ledgergut reimbursement states."""

    NOT_REIMBURSED = "not_reimbursed"
    REIMBURSED = "reimbursed"
    MAYBE_REIMBURSED = "maybe_reimbursed"
    NOT_REIMBURSABLE = "not_reimbursable"
    UNKNOWN = "unknown"


class BillableStatus(str, Enum):
    """Canonical Ledgergut billable states."""

    BILLABLE = "billable"
    NOT_BILLABLE = "not_billable"
    MAYBE_BILLABLE = "maybe_billable"
    ALREADY_INVOICED = "already_invoiced"
    TAX_ONLY = "tax_only"


@dataclass(frozen=True)
class ReceiptLineItem:
    name: str
    quantity: Decimal | int | float | str
    unit_price: Decimal | int | float | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", _coerce_decimal(self.quantity, "quantity"))
        object.__setattr__(self, "unit_price", _coerce_decimal(self.unit_price, "unit_price"))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "quantity": _serialize_decimal(self.quantity),
            "unit_price": _serialize_decimal(self.unit_price),
        }


@dataclass(frozen=True)
class TaxLine:
    label: str
    amount: Decimal | int | float | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", _coerce_decimal(self.amount, "amount"))

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "amount": _serialize_decimal(self.amount),
        }


@dataclass(frozen=True)
class ReceiptExtraction:
    vendor_name: str | None = None
    receipt_date: date | str | None = None
    line_items: tuple[ReceiptLineItem, ...] = ()
    subtotal: Decimal | int | float | str | None = None
    tax_lines: tuple[TaxLine, ...] = ()
    tax_amount: Decimal | int | float | str | None = None
    total_amount: Decimal | int | float | str | None = None
    payment_method: str | None = None
    receipt_number: str | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_date", _coerce_date(self.receipt_date, "receipt_date"))
        object.__setattr__(self, "subtotal", _coerce_decimal(self.subtotal, "subtotal"))
        object.__setattr__(self, "tax_amount", _coerce_decimal(self.tax_amount, "tax_amount"))
        object.__setattr__(self, "total_amount", _coerce_decimal(self.total_amount, "total_amount"))
        object.__setattr__(self, "line_items", tuple(self.line_items))
        object.__setattr__(self, "tax_lines", tuple(self.tax_lines))
        for line_item in self.line_items:
            if not isinstance(line_item, ReceiptLineItem):
                raise TypeError("line_items must contain ReceiptLineItem values.")
        for tax_line in self.tax_lines:
            if not isinstance(tax_line, TaxLine):
                raise TypeError("tax_lines must contain TaxLine values.")

    def to_dict(self) -> dict[str, object]:
        return {
            "vendor_name": self.vendor_name,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "line_items": [line_item.to_dict() for line_item in self.line_items],
            "subtotal": (
                _serialize_decimal(self.subtotal) if self.subtotal is not None else None
            ),
            "tax_lines": [tax_line.to_dict() for tax_line in self.tax_lines],
            "tax_amount": (
                _serialize_decimal(self.tax_amount) if self.tax_amount is not None else None
            ),
            "total_amount": (
                _serialize_decimal(self.total_amount)
                if self.total_amount is not None
                else None
            ),
            "payment_method": self.payment_method,
            "receipt_number": self.receipt_number,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class ValidationFinding:
    rule_id: str
    fields: tuple[str, ...]
    severity: str
    message: str
    requires_human_review: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", tuple(self.fields))
        if self.severity not in {"error", "warning"}:
            raise ValueError("severity must be 'error' or 'warning'.")

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "fields": list(self.fields),
            "severity": self.severity,
            "message": self.message,
            "requires_human_review": self.requires_human_review,
        }


@dataclass(frozen=True)
class ReceiptRecord:
    submitted_by: str
    description: str
    receipt: ReceiptExtraction
    record_id: str | None = None
    collar_id: str = "black_collar"
    submitted_at: datetime | str | None = None
    project_name: str | None = None
    expense_category: str | None = None
    currency: str | None = None
    paid_by: PaidBy | str = PaidBy.UNKNOWN
    reimbursement_status: ReimbursementStatus | str = ReimbursementStatus.UNKNOWN
    billable_status: BillableStatus | str | None = None
    invoice_id: str | None = None
    payment_notes: str | None = None
    assignment_confidence: float | int | str | None = None
    ocr_confidence: Mapping[str, float | int | str] = field(default_factory=dict)
    needs_user_review: bool = False
    review_notes: str | None = None
    status: str = "pending_review"
    created_at: datetime | str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.receipt, ReceiptExtraction):
            raise TypeError("receipt must be a ReceiptExtraction instance.")
        object.__setattr__(
            self, "submitted_at", _coerce_datetime(self.submitted_at, "submitted_at")
        )
        object.__setattr__(self, "created_at", _coerce_datetime(self.created_at, "created_at"))
        object.__setattr__(
            self,
            "assignment_confidence",
            _coerce_confidence(self.assignment_confidence, "assignment_confidence"),
        )
        object.__setattr__(self, "paid_by", PaidBy(self.paid_by))
        object.__setattr__(
            self,
            "reimbursement_status",
            ReimbursementStatus(self.reimbursement_status),
        )
        if self.billable_status is not None:
            object.__setattr__(self, "billable_status", BillableStatus(self.billable_status))
        normalized_confidence = {
            field_name: _coerce_confidence(score, f"ocr_confidence.{field_name}")
            for field_name, score in dict(self.ocr_confidence).items()
        }
        object.__setattr__(
            self,
            "ocr_confidence",
            MappingProxyType(normalized_confidence),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "collar_id": self.collar_id,
            "submitted_by": self.submitted_by,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "description": self.description,
            "project_name": self.project_name,
            "expense_category": self.expense_category,
            "currency": self.currency,
            "paid_by": self.paid_by.value,
            "reimbursement_status": self.reimbursement_status.value,
            "billable_status": (
                self.billable_status.value if self.billable_status is not None else None
            ),
            "invoice_id": self.invoice_id,
            "payment_notes": self.payment_notes,
            "assignment_confidence": self.assignment_confidence,
            "receipt": self.receipt.to_dict(),
            "ocr_confidence": dict(self.ocr_confidence),
            "needs_user_review": self.needs_user_review,
            "review_notes": self.review_notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
