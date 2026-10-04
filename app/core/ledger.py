"""Running invoice/payment ledger calculations for the Black Office."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.models import Invoice, InvoiceStatus, Payment


@dataclass(frozen=True)
class InvoicePaymentSummary:
    invoice_id: str
    invoiced: Decimal
    paid: Decimal
    balance: Decimal
    overpayment: Decimal
    currency: str
    status: InvoiceStatus


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
