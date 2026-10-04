from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.core.job_lifecycle import (
    draft_job_plan,
    draft_project_invoice,
    ingest_receipt_for_project,
    persist_job_plan,
    record_payment,
    record_project_work,
)
from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Agreement, AgreementStatus, ChangeOrderStatus, InvoiceStatus
from app.ledgergut.models import BillableStatus, ReceiptExtraction, ReceiptLineItem, ReceiptRecord
from app.packrat.service import MaterialRequirementInput
from app.signor.service import draft_change_order


def _agreement() -> Agreement:
    return Agreement(
        agreement_id="AGR-GOLDEN",
        business_id="BIZ-1",
        project_id="PRJ-1",
        title="Frame utility wall",
        scope="Frame a non-load-bearing utility wall and install blocking.",
        amount=None,
        currency="CAD",
        status=AgreementStatus.ACCEPTED,
    )


def test_job_survives_estimate_receipt_work_invoice_and_payment():
    store = InMemoryBlackOfficeStore.create()
    agreement = _agreement()
    store.agreements.save(agreement)

    plan = draft_job_plan(
        business_id="BIZ-1",
        agreement=agreement,
        labour_hours="8",
        labour_rate="40",
        materials=(
            MaterialRequirementInput(
                description="2x4x8 SPF lumber",
                quantity="10",
                unit="ea",
                estimated_unit_cost="4.50",
            ),
        ),
        assumptions="Existing floor and ceiling are suitable for fastening.",
    )
    assert plan.errors == ()
    assert plan.estimate is not None
    assert plan.estimate.total_estimate == Decimal("365.00")
    persisted = persist_job_plan(store, plan, approve_materials=True)
    assert persisted.material_plan is not None
    assert persisted.material_plan.approved is True

    receipt = ReceiptRecord(
        record_id="REC-001",
        submitted_by="Steve",
        description="Framing lumber",
        currency="CAD",
        billable_status=BillableStatus.BILLABLE,
        receipt=ReceiptExtraction(
            vendor_name="Building Supply",
            receipt_date=date(2026, 10, 4),
            line_items=(ReceiptLineItem(name="2x4x8 SPF lumber", quantity="6", unit_price="4.50"),),
            subtotal="27.00",
            total_amount="27.00",
            currency="CAD",
        ),
    )
    applied = ingest_receipt_for_project(
        store,
        receipt,
        business_id="BIZ-1",
        project_id="PRJ-1",
    )
    assert applied.expense.amount == Decimal("27.00")
    assert len(applied.reconciliation.matches) == 1
    shopping_item = store.shopping_items.list_for_business("BIZ-1")[0]
    assert shopping_item.quantity_acquired == Decimal("6")
    assert shopping_item.quantity_remaining == Decimal("4")
    assert shopping_item.actual_cost == Decimal("27.00")

    work = record_project_work(
        store,
        business_id="BIZ-1",
        project_id="PRJ-1",
        description="Frame wall and install blocking",
        hours="7.5",
        occurred_on=date(2026, 10, 5),
    )
    assert work.errors == ()
    assert work.work_log is not None
    assert work.work_log.hours == Decimal("7.5")

    change = draft_change_order(
        agreement=agreement,
        business_id="BIZ-1",
        title="Additional backing",
        scope="Add backing requested after framing began.",
        amount="50",
    )
    assert change.errors == ()
    assert change.change_order is not None
    store.change_orders.save(replace(change.change_order, status=ChangeOrderStatus.APPROVED))

    invoice_result = draft_project_invoice(
        store,
        business_id="BIZ-1",
        agreement=agreement,
        client_id="CLI-1",
        labour_rate="40",
        include_agreement_amount=False,
        due_date=date(2026, 10, 20),
    )
    assert invoice_result.errors == ()
    assert invoice_result.invoice is not None
    invoice = invoice_result.invoice
    assert invoice.total == Decimal("377.00")
    assert {line.source_type for line in invoice.line_items} == {"expense", "work_log", "change_order"}

    first_payment = record_payment(store, invoice=invoice, amount="100", received_on=date(2026, 10, 10))
    assert first_payment.summary.status == InvoiceStatus.PARTIALLY_PAID
    assert first_payment.summary.balance == Decimal("277.00")
    stored = store.invoices.get(invoice.invoice_id, "BIZ-1")
    assert stored is not None and stored.status == InvoiceStatus.PARTIALLY_PAID

    final_payment = record_payment(store, invoice=first_payment.invoice, amount="277", received_on=date(2026, 10, 12))
    assert final_payment.summary.status == InvoiceStatus.PAID
    assert final_payment.summary.balance == Decimal("0.00")
    stored = store.invoices.get(invoice.invoice_id, "BIZ-1")
    assert stored is not None and stored.status == InvoiceStatus.PAID


def test_unassigned_expense_is_not_silently_pulled_into_project_invoice():
    store = InMemoryBlackOfficeStore.create()
    agreement = _agreement()
    store.agreements.save(agreement)

    receipt = ReceiptRecord(
        record_id="REC-UNASSIGNED",
        submitted_by="Steve",
        description="Mystery purchase",
        currency="CAD",
        billable_status=BillableStatus.BILLABLE,
        receipt=ReceiptExtraction(total_amount="99.00", currency="CAD"),
    )
    from app.ledgergut.office_adapter import receipt_record_to_expense
    store.expenses.save(receipt_record_to_expense(receipt, business_id="BIZ-1", project_id=None))

    work = record_project_work(
        store,
        business_id="BIZ-1",
        project_id="PRJ-1",
        description="Known labour",
        hours="1",
    )
    assert work.work_log is not None

    result = draft_project_invoice(
        store,
        business_id="BIZ-1",
        agreement=agreement,
        client_id="CLI-1",
        labour_rate="40",
        include_agreement_amount=False,
    )
    assert result.invoice is not None
    assert result.invoice.total == Decimal("40.00")
    assert all(line.source_id != "REC-UNASSIGNED" for line in result.invoice.line_items)
