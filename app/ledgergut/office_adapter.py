"""Bridge Ledgergut receipt records into shared Black Office expenses."""

from __future__ import annotations

from decimal import Decimal

from app.core.models import Expense
from app.ledgergut.models import BillableStatus, ReceiptRecord


def receipt_record_to_expense(
    record: ReceiptRecord,
    *,
    business_id: str,
    project_id: str | None = None,
) -> Expense:
    """Convert a confirmed Ledgergut receipt record into an Office Expense.

    The adapter is intentionally side-effect free. Persisting the returned
    Expense is the responsibility of the shared Black Office store.
    """
    total = record.receipt.total_amount
    if total is None:
        raise ValueError("receipt total_amount is required to create an Expense")

    currency = record.currency or record.receipt.currency
    if not currency:
        raise ValueError("currency is required to create an Expense")

    billable: bool | None
    if record.billable_status in {
        BillableStatus.BILLABLE,
        BillableStatus.ALREADY_INVOICED,
        BillableStatus.TAX_ONLY,
    }:
        billable = True
    elif record.billable_status == BillableStatus.NOT_BILLABLE:
        billable = False
    else:
        billable = None

    expense_id = record.record_id or ""
    if not expense_id:
        raise ValueError("record_id is required to create an Expense")

    return Expense(
        expense_id=expense_id,
        business_id=business_id,
        project_id=project_id,
        amount=Decimal(total),
        currency=currency.upper(),
        description=record.description,
        source_goblin="ledgergut",
        source_record_id=record.record_id,
        occurred_on=record.receipt.receipt_date,
        billable=billable,
    )
