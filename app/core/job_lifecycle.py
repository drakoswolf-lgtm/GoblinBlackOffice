"""Golden-path orchestration across Black Office specialists.

This module is deliberately thin. The Office owns the shared records while each
goblin keeps its specialist rules. These functions provide the hand-offs that
turn isolated workflows into one surviving job record.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
import uuid

from app.core.ledger import InvoicePaymentSummary, summarize_invoice_payments
from app.core.models import Agreement, Estimate, Expense, Invoice, MaterialPlan, Payment, ShoppingListItem
from app.core.storage import BlackOfficeStore
from app.ledgergut.models import ReceiptRecord
from app.ledgergut.office_adapter import receipt_record_to_expense
from app.packrat.service import (
    MaterialRequirementInput,
    ReceiptReconciliation,
    draft_material_plan,
    reconcile_receipt,
)
from app.patch.service import WorkLogResult, record_work
from app.squarmish.service import InvoiceDraftResult, draft_invoice


def _decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc


@dataclass(frozen=True)
class JobPlanDraft:
    estimate: Estimate | None
    material_plan: MaterialPlan | None
    shopping_items: tuple[ShoppingListItem, ...]
    errors: tuple[str, ...]
    review_notes: tuple[str, ...]


@dataclass(frozen=True)
class ReceiptAppliedResult:
    expense: Expense
    reconciliation: ReceiptReconciliation


@dataclass(frozen=True)
class PaymentRecordedResult:
    payment: Payment
    invoice: Invoice
    summary: InvoicePaymentSummary


def draft_job_plan(
    *,
    business_id: str,
    agreement: Agreement,
    labour_hours: Decimal | int | float | str | None,
    labour_rate: Decimal | int | float | str | None,
    materials: tuple[MaterialRequirementInput, ...],
    other_cost: Decimal | int | float | str = "0",
    assumptions: str = "",
) -> JobPlanDraft:
    errors: list[str] = []
    notes: list[str] = []
    if agreement.business_id != business_id:
        errors.append("Agreement does not belong to this business.")

    parsed_hours: Decimal | None = None
    parsed_rate: Decimal | None = None
    if labour_hours is not None and str(labour_hours).strip() != "":
        try:
            parsed_hours = _decimal(labour_hours, "labour_hours")
            if parsed_hours < 0:
                errors.append("Estimated labour hours cannot be negative.")
        except ValueError as exc:
            errors.append(str(exc))
    if labour_rate is not None and str(labour_rate).strip() != "":
        try:
            parsed_rate = _decimal(labour_rate, "labour_rate")
            if parsed_rate < 0:
                errors.append("Labour rate cannot be negative.")
        except ValueError as exc:
            errors.append(str(exc))
    if (parsed_hours is None) != (parsed_rate is None):
        errors.append("Estimated labour requires both hours and rate, or neither.")

    try:
        parsed_other = _decimal(other_cost, "other_cost")
        if parsed_other < 0:
            errors.append("Other estimated cost cannot be negative.")
    except ValueError as exc:
        parsed_other = Decimal("0")
        errors.append(str(exc))

    if errors:
        return JobPlanDraft(None, None, (), tuple(errors), tuple(notes))

    estimate_id = f"EST-{uuid.uuid4().hex[:12].upper()}"
    material_plan = None
    shopping_items: tuple[ShoppingListItem, ...] = ()
    if materials:
        material_result = draft_material_plan(
            business_id=business_id,
            project_id=agreement.project_id,
            title=f"{agreement.title} materials",
            requirements=materials,
            agreement_id=agreement.agreement_id,
            estimate_id=estimate_id,
            notes="Editable material plan derived for human review.",
        )
        if material_result.errors:
            return JobPlanDraft(None, None, (), material_result.errors, tuple(notes))
        material_plan = material_result.plan
        shopping_items = material_result.items

    materials_subtotal = Decimal("0.00")
    unknown_costs: list[str] = []
    for requirement in materials:
        if requirement.estimated_unit_cost is None:
            unknown_costs.append(requirement.description)
            continue
        materials_subtotal += requirement.quantity * requirement.estimated_unit_cost
    materials_subtotal = materials_subtotal.quantize(Decimal("0.01"))
    if unknown_costs:
        notes.append(
            "Estimate excludes unknown unit costs for: " + ", ".join(unknown_costs) + "."
        )

    labour_subtotal = Decimal("0.00")
    if parsed_hours is not None and parsed_rate is not None:
        labour_subtotal = (parsed_hours * parsed_rate).quantize(Decimal("0.01"))

    total = (labour_subtotal + materials_subtotal + parsed_other).quantize(Decimal("0.01"))
    estimate = Estimate(
        estimate_id=estimate_id,
        business_id=business_id,
        project_id=agreement.project_id,
        agreement_id=agreement.agreement_id,
        currency=agreement.currency.upper(),
        labour_hours_estimate=parsed_hours,
        labour_rate=parsed_rate,
        labour_subtotal=labour_subtotal,
        materials_subtotal=materials_subtotal,
        other_subtotal=parsed_other.quantize(Decimal("0.01")),
        total_estimate=total,
        assumptions=assumptions.strip(),
    )
    return JobPlanDraft(
        estimate=estimate,
        material_plan=material_plan,
        shopping_items=shopping_items,
        errors=(),
        review_notes=tuple(notes),
    )


def persist_job_plan(
    store: BlackOfficeStore,
    draft: JobPlanDraft,
    *,
    approve_materials: bool = False,
) -> JobPlanDraft:
    if draft.errors or draft.estimate is None:
        raise ValueError("Cannot persist an invalid job plan draft.")
    store.estimates.save(draft.estimate)
    if draft.material_plan is None:
        return draft
    plan = replace(draft.material_plan, approved=approve_materials)
    store.material_plans.save(plan)
    for item in draft.shopping_items:
        store.shopping_items.save(item)
    return replace(draft, material_plan=plan)


def ingest_receipt_for_project(
    store: BlackOfficeStore,
    record: ReceiptRecord,
    *,
    business_id: str,
    project_id: str,
) -> ReceiptAppliedResult:
    expense = receipt_record_to_expense(record, business_id=business_id, project_id=project_id)
    store.expenses.save(expense)

    approved_plan_ids = {
        plan.material_plan_id
        for plan in store.material_plans.list_for_business(business_id)
        if plan.project_id == project_id and plan.approved
    }
    project_items = tuple(
        item
        for item in store.shopping_items.list_for_business(business_id)
        if item.project_id == project_id and item.material_plan_id in approved_plan_ids
    )
    reconciliation = reconcile_receipt(record, project_items)
    for item in reconciliation.items:
        store.shopping_items.save(item)
    return ReceiptAppliedResult(expense=expense, reconciliation=reconciliation)


def record_project_work(
    store: BlackOfficeStore,
    *,
    business_id: str,
    project_id: str,
    description: str,
    hours,
    occurred_on: date | None = None,
    billable: bool = True,
    rate_override=None,
) -> WorkLogResult:
    result = record_work(
        business_id=business_id,
        project_id=project_id,
        description=description,
        hours=hours,
        occurred_on=occurred_on,
        billable=billable,
        rate_override=rate_override,
    )
    if result.work_log is not None:
        store.work_logs.save(result.work_log)
    return result


def draft_project_invoice(
    store: BlackOfficeStore,
    *,
    business_id: str,
    agreement: Agreement,
    client_id: str,
    labour_rate=None,
    include_agreement_amount: bool = True,
    due_date: date | None = None,
) -> InvoiceDraftResult:
    expenses = tuple(
        expense
        for expense in store.expenses.list_for_business(business_id)
        if expense.project_id == agreement.project_id
    )
    work_logs = tuple(
        log
        for log in store.work_logs.list_for_business(business_id)
        if log.project_id == agreement.project_id
    )
    changes = tuple(
        change
        for change in store.change_orders.list_for_business(business_id)
        if change.project_id == agreement.project_id and change.agreement_id == agreement.agreement_id
    )
    result = draft_invoice(
        business_id=business_id,
        agreement=agreement,
        client_id=client_id,
        expenses=expenses,
        work_logs=work_logs,
        labour_rate=labour_rate,
        change_orders=changes,
        include_agreement_amount=include_agreement_amount,
        due_date=due_date,
    )
    if result.invoice is not None:
        store.invoices.save(result.invoice)
    return result


def record_payment(
    store: BlackOfficeStore,
    *,
    invoice: Invoice,
    amount,
    received_on: date | None = None,
    currency: str | None = None,
) -> PaymentRecordedResult:
    parsed_amount = _decimal(amount, "amount")
    if parsed_amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    payment_currency = (currency or invoice.currency).upper()
    if payment_currency != invoice.currency.upper():
        raise ValueError("Payment currency must match the invoice currency.")
    payment = Payment(
        payment_id=f"PAY-{uuid.uuid4().hex[:12].upper()}",
        business_id=invoice.business_id,
        invoice_id=invoice.invoice_id,
        amount=parsed_amount.quantize(Decimal("0.01")),
        currency=payment_currency,
        received_on=received_on,
    )
    store.payments.save(payment)
    payments = tuple(store.payments.list_for_business(invoice.business_id))
    summary = summarize_invoice_payments(invoice, payments)
    updated_invoice = replace(invoice, status=summary.status)
    store.invoices.save(updated_invoice)
    return PaymentRecordedResult(payment, updated_invoice, summary)
