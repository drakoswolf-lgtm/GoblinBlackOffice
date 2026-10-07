"""Helpers to map HTML form data into Ledgergut domain models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from app.ledgergut.models import (
    BillableStatus,
    PaidBy,
    ReceiptExtraction,
    ReceiptLineItem,
    ReceiptRecord,
    ReimbursementStatus,
)


def _parse_money(raw: str, field_name: str) -> tuple[Decimal | None, str | None]:
    """Return ``(Decimal, None)`` on success or ``(None, error_message)`` on failure."""
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        return Decimal(raw), None
    except InvalidOperation:
        return None, f"{field_name}: '{raw}' is not a valid amount."


def _parse_date(raw: str, field_name: str) -> tuple[date | None, str | None]:
    """Return ``(date, None)`` on success or ``(None, error_message)`` on failure."""
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        return date.fromisoformat(raw), None
    except ValueError:
        return None, f"{field_name}: '{raw}' is not a valid ISO date (YYYY-MM-DD)."


def _safe_enum(cls, raw: str, default):
    try:
        return cls(raw.strip())
    except (ValueError, AttributeError):
        return default


def _parse_line_items(raw: str) -> tuple[tuple[ReceiptLineItem, ...], list[str]]:
    items: list[ReceiptLineItem] = []
    errors: list[str] = []
    for number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3:
            errors.append(
                f"Purchased item line {number}: use description | quantity | unit price."
            )
            continue
        name, quantity_raw, price_raw = parts
        if not name:
            errors.append(f"Purchased item line {number}: description is required.")
            continue
        try:
            items.append(
                ReceiptLineItem(
                    name=name,
                    quantity=quantity_raw,
                    unit_price=price_raw,
                )
            )
        except ValueError as exc:
            errors.append(f"Purchased item line {number}: {exc}")
    return tuple(items), errors


def build_models(
    form: dict[str, str],
) -> tuple[ReceiptRecord | None, list[str]]:
    """Convert raw form string data into a ``ReceiptRecord``.

    Returns ``(ReceiptRecord, [])`` on success or ``(None, [errors])`` when any
    input cannot be parsed safely.  Malformed money or date values produce
    user-facing error strings rather than exceptions.
    """
    errors: list[str] = []

    subtotal, err = _parse_money(form.get("subtotal", ""), "Subtotal")
    if err:
        errors.append(err)
    tax_amount, err = _parse_money(form.get("tax_amount", ""), "Tax amount")
    if err:
        errors.append(err)
    total_amount, err = _parse_money(form.get("total_amount", ""), "Total amount")
    if err:
        errors.append(err)

    receipt_date, err = _parse_date(form.get("receipt_date", ""), "Receipt date")
    if err:
        errors.append(err)

    line_items, line_item_errors = _parse_line_items(form.get("line_items_text", ""))
    errors.extend(line_item_errors)

    if errors:
        return None, errors

    currency = form.get("currency", "CAD").strip() or "CAD"

    extraction = ReceiptExtraction(
        vendor_name=form.get("vendor_name", "").strip() or None,
        receipt_date=receipt_date,
        line_items=line_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        receipt_number=form.get("receipt_number", "").strip() or None,
        currency=currency,
    )

    paid_by = _safe_enum(PaidBy, form.get("paid_by", ""), PaidBy.UNKNOWN)
    reimbursement_status = _safe_enum(
        ReimbursementStatus,
        form.get("reimbursement_status", ""),
        ReimbursementStatus.UNKNOWN,
    )
    billable_status_raw = form.get("billable_status", "").strip()
    billable_status = _safe_enum(BillableStatus, billable_status_raw, None) if billable_status_raw else None

    submitted_by = form.get("submitted_by", "web_user").strip() or "web_user"
    description = form.get("description", "").strip() or "(no description)"
    project_name = form.get("project_name", "").strip() or None
    expense_category = form.get("expense_category", "").strip() or None
    invoice_id = form.get("invoice_id", "").strip() or None

    try:
        record = ReceiptRecord(
            submitted_by=submitted_by,
            description=description,
            receipt=extraction,
            project_name=project_name,
            expense_category=expense_category,
            currency=currency,
            paid_by=paid_by,
            reimbursement_status=reimbursement_status,
            billable_status=billable_status,
            invoice_id=invoice_id,
        )
    except (ValueError, TypeError) as exc:
        errors.append(str(exc))
        return None, errors

    return record, []
