"""Squarmish invoice drafting service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.core.models import Agreement, Expense, Invoice, InvoiceStatus


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    amount: Decimal
    source_type: str
    source_id: str


@dataclass(frozen=True)
class InvoiceDraftResult:
    invoice: Invoice | None
    lines: tuple[InvoiceLine, ...]
    errors: tuple[str, ...]
    review_notes: tuple[str, ...]


def draft_invoice(
    *,
    business_id: str,
    agreement: Agreement,
    client_id: str,
    expenses: tuple[Expense, ...] = (),
    include_agreement_amount: bool = True,
    due_date: date | None = None,
) -> InvoiceDraftResult:
    errors: list[str] = []
    notes: list[str] = []

    if agreement.business_id != business_id:
        errors.append("Agreement does not belong to this business.")
    if not client_id.strip():
        errors.append("Client is required before an invoice can be drafted.")

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

    if not lines and not errors:
        errors.append("Invoice has no confirmed billable lines.")

    if errors:
        return InvoiceDraftResult(None, tuple(lines), tuple(errors), tuple(notes))

    total = sum((line.amount for line in lines), Decimal("0.00"))
    notes.append("Tax has not been applied. Review line-level tax treatment before issuing.")
    invoice = Invoice(
        invoice_id=f"SQ-{uuid.uuid4().hex[:12].upper()}",
        business_id=business_id,
        project_id=agreement.project_id,
        client_id=client_id.strip(),
        total=total,
        currency=agreement.currency.upper(),
        status=InvoiceStatus.DRAFT,
        due_date=due_date,
    )
    return InvoiceDraftResult(invoice, tuple(lines), (), tuple(notes))
