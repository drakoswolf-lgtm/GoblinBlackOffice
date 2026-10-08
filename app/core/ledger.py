"""Running ledger calculations for the Black Office.

The ledger is a derived view over authoritative Office records. It is not a
second mutable accounting store that can drift away from invoices, payments,
and expenses.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.models import Expense, Invoice, InvoiceStatus, Payment


@dataclass(frozen=True)
class InvoicePaymentSummary:
    invoice_id: str
    invoiced: Decimal
    paid: Decimal
    balance: Decimal
    overpayment: Decimal
    currency: str
    status: InvoiceStatus


@dataclass(frozen=True)
class LedgerSummary:
    business_id: str
    project_id: str | None
    invoiced: Decimal
    paid: Decimal
    outstanding: Decimal
    expenses: Decimal
    net_cash: Decimal
    currency: str


def summarize_invoice_payments(
    invoice: Invoice,
    payments: tuple[Payment, ...],
) -> InvoicePaymentSummary:
    applied = Decimal("0.00")
    for payment in payments:
        if payment.business_id != invoice.business_id:
            continue
        if payment.invoice_id != invoice.invoice_id:
            continue
        if payment.currency.upper() != invoice.currency.upper():
            continue
        applied += payment.amount

    applied = applied.quantize(Decimal("0.01"))
    balance = max(Decimal("0.00"), invoice.total - applied).quantize(Decimal("0.01"))
    overpayment = max(Decimal("0.00"), applied - invoice.total).quantize(Decimal("0.01"))

    if applied <= 0:
        status = invoice.status
    elif balance == 0:
        status = InvoiceStatus.PAID
    else:
        status = InvoiceStatus.PARTIALLY_PAID

    return InvoicePaymentSummary(
        invoice_id=invoice.invoice_id,
        invoiced=invoice.total.quantize(Decimal("0.01")),
        paid=applied,
        balance=balance,
        overpayment=overpayment,
        currency=invoice.currency.upper(),
        status=status,
    )


def _ledger_summary(
    *,
    business_id: str,
    project_id: str | None,
    invoices: tuple[Invoice, ...],
    payments: tuple[Payment, ...],
    expenses: tuple[Expense, ...],
    currency: str,
) -> LedgerSummary:
    resolved_currency = currency.upper()
    countable_statuses = {
        InvoiceStatus.APPROVED,
        InvoiceStatus.SENT,
        InvoiceStatus.DUE,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.PAID,
        InvoiceStatus.OVERDUE,
    }
    relevant_invoices = tuple(
        invoice
        for invoice in invoices
        if invoice.business_id == business_id
        and (project_id is None or invoice.project_id == project_id)
        and invoice.currency.upper() == resolved_currency
        and invoice.status in countable_statuses
    )
    invoice_ids = {invoice.invoice_id for invoice in relevant_invoices}

    invoiced = sum((invoice.total for invoice in relevant_invoices), Decimal("0.00"))
    paid = sum(
        (
            payment.amount
            for payment in payments
            if payment.business_id == business_id
            and payment.invoice_id in invoice_ids
            and payment.currency.upper() == resolved_currency
        ),
        Decimal("0.00"),
    )
    expense_total = sum(
        (
            expense.amount
            for expense in expenses
            if expense.business_id == business_id
            and (project_id is None or expense.project_id == project_id)
            and expense.currency.upper() == resolved_currency
        ),
        Decimal("0.00"),
    )
    invoiced = invoiced.quantize(Decimal("0.01"))
    paid = paid.quantize(Decimal("0.01"))
    expense_total = expense_total.quantize(Decimal("0.01"))
    outstanding = max(Decimal("0.00"), invoiced - paid).quantize(Decimal("0.01"))
    net_cash = (paid - expense_total).quantize(Decimal("0.01"))
    return LedgerSummary(
        business_id=business_id,
        project_id=project_id,
        invoiced=invoiced,
        paid=paid,
        outstanding=outstanding,
        expenses=expense_total,
        net_cash=net_cash,
        currency=resolved_currency,
    )


def summarize_project_ledger(
    *,
    business_id: str,
    project_id: str,
    invoices: tuple[Invoice, ...],
    payments: tuple[Payment, ...],
    expenses: tuple[Expense, ...],
    currency: str = "CAD",
) -> LedgerSummary:
    return _ledger_summary(
        business_id=business_id,
        project_id=project_id,
        invoices=invoices,
        payments=payments,
        expenses=expenses,
        currency=currency,
    )


def summarize_business_ledger(
    *,
    business_id: str,
    invoices: tuple[Invoice, ...],
    payments: tuple[Payment, ...],
    expenses: tuple[Expense, ...],
    currency: str = "CAD",
) -> LedgerSummary:
    return _ledger_summary(
        business_id=business_id,
        project_id=None,
        invoices=invoices,
        payments=payments,
        expenses=expenses,
        currency=currency,
    )
