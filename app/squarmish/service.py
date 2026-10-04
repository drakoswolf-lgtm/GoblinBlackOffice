"""Squarmish invoice drafting service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.models import (
    Agreement,
    ChangeOrder,
    ChangeOrderStatus,
    Expense,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    WorkLog,
)

InvoiceLine = InvoiceLineItem


@dataclass(frozen=True)
class InvoiceDraftResult:
    invoice: Invoice | None
    lines: tuple[InvoiceLine, ...]
    errors: tuple[str, ...]
    review_notes: tuple[str, ...]


def _decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc


def draft_invoice(
    *,
    business_id: str,
    agreement: Agreement,
    client_id: str,
    expenses: tuple[Expense, ...] = (),
    work_logs: tuple[WorkLog, ...] = (),
    labour_rate: Decimal | int | float | str | None = None,
    change_orders: tuple[ChangeOrder, ...] = (),
    include_agreement_amount: bool = True,
    due_date: date | None = None,
) -> InvoiceDraftResult:
    errors: list[str] = []
    notes: list[str] = []

    if agreement.business_id != business_id:
        errors.append("Agreement does not belong to this business.")
    if not client_id.strip():
        errors.append("Client is required before an invoice can be drafted.")

    default_labour_rate: Decimal | None = None
    if labour_rate is not None and str(labour_rate).strip() != "":
        try:
            default_labour_rate = _decimal(labour_rate, "labour_rate")
            if default_labour_rate < 0:
                errors.append("Labour rate cannot be negative.")
        except ValueError as exc:
            errors.append(str(exc))

    lines: list[InvoiceLine] = []
    if include_agreement_amount:
        if agreement.amount is None:
            errors.append("Agreement has no price to invoice.")
        else:
            lines.append(
                InvoiceLine(
                    description=agreement.title,
                    amount=agreement.amount,
                    source_type="agreement",
                    source_id=agreement.agreement_id,
                )
            )

    for expense in expenses:
        if expense.business_id != business_id:
            errors.append(f"Expense {expense.expense_id} belongs to another business.")
            continue
        if expense.project_id not in {None, agreement.project_id}:
            errors.append(f"Expense {expense.expense_id} belongs to another project.")
            continue
        if expense.currency.upper() != agreement.currency.upper():
            errors.append(f"Expense {expense.expense_id} uses a different currency.")
            continue
        if expense.billable is not True:
            notes.append(f"Expense {expense.expense_id} is not confirmed billable and was excluded.")
            continue
        lines.append(
            InvoiceLine(
                description=expense.description,
                amount=expense.amount,
                source_type="expense",
                source_id=expense.expense_id,
            )
        )

    included_work_logs = 0
    for work_log in work_logs:
        if work_log.business_id != business_id:
            errors.append(f"Work log {work_log.work_log_id} belongs to another business.")
            continue
        if work_log.project_id != agreement.project_id:
            errors.append(f"Work log {work_log.work_log_id} belongs to another project.")
            continue
        if not work_log.billable:
            notes.append(f"Work log {work_log.work_log_id} is not billable and was excluded.")
            continue
        rate = work_log.rate_override if work_log.rate_override is not None else default_labour_rate
        if rate is None:
            errors.append(f"Work log {work_log.work_log_id} has no billable labour rate.")
            continue
        amount = (work_log.hours * rate).quantize(Decimal("0.01"))
        lines.append(
            InvoiceLine(
                description=f"Labour: {work_log.description} ({work_log.hours} h @ {rate}/h)",
                amount=amount,
                source_type="work_log",
                source_id=work_log.work_log_id,
            )
        )
        included_work_logs += 1

    for change in change_orders:
        if change.business_id != business_id:
            errors.append(f"Change order {change.change_order_id} belongs to another business.")
            continue
        if change.project_id != agreement.project_id or change.agreement_id != agreement.agreement_id:
            errors.append(f"Change order {change.change_order_id} belongs to another agreement or project.")
            continue
        if change.status != ChangeOrderStatus.APPROVED:
            notes.append(f"Change order {change.change_order_id} is not approved and was excluded.")
            continue
        if change.currency.upper() != agreement.currency.upper():
            errors.append(f"Change order {change.change_order_id} uses a different currency.")
            continue
        if change.amount is None:
            errors.append(f"Approved change order {change.change_order_id} has no amount.")
            continue
        lines.append(
            InvoiceLine(
                description=f"Approved change: {change.title}",
                amount=change.amount,
                source_type="change_order",
                source_id=change.change_order_id,
            )
        )

    if include_agreement_amount and included_work_logs:
        notes.append("Agreement amount and actual labour are both included; confirm this matches the pricing model before issuing.")

    if not lines and not errors:
        errors.append("Invoice has no confirmed billable lines.")

    if errors:
        return InvoiceDraftResult(None, tuple(lines), tuple(errors), tuple(notes))

    subtotal = sum((line.amount for line in lines), Decimal("0.00")).quantize(Decimal("0.01"))
    notes.append("Tax has not been applied. Review line-level tax treatment before issuing.")
    invoice = Invoice(
        invoice_id=f"SQ-{uuid.uuid4().hex[:12].upper()}",
        business_id=business_id,
        project_id=agreement.project_id,
        client_id=client_id.strip(),
        total=subtotal,
        currency=agreement.currency.upper(),
        status=InvoiceStatus.DRAFT,
        due_date=due_date,
        agreement_id=agreement.agreement_id,
        subtotal=subtotal,
        tax_total=None,
        line_items=tuple(lines),
        review_notes=tuple(notes),
    )
    return InvoiceDraftResult(invoice, tuple(lines), (), tuple(notes))
