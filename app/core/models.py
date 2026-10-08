"""Shared Black Office domain models.

The Black Office owns business data. Goblins operate on these shared records
rather than maintaining isolated copies of clients, projects, agreements,
expenses, invoices, and payments.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class RecordStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AgreementStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    SUPERSEDED = "superseded"


class ChangeOrderStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    DECLINED = "declined"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    DUE = "due"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


@dataclass(frozen=True)
class User:
    user_id: str
    business_id: str
    email: str
    password_hash: str
    display_name: str
    onboarding_complete: bool = False
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Business:
    business_id: str
    name: str
    reporting_currency: str = "CAD"
    operating_name: str | None = None
    business_type: str | None = None
    legal_structure: str | None = None
    operating_model: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    website: str | None = None
    service_area: str | None = None
    business_phone: str | None = None
    business_email: str | None = None
    parent_business_name: str | None = None
    subsidiaries: str | None = None
    franchise_status: str | None = None
    franchisor_name: str | None = None
    fiscal_year_end: str | None = None
    tax_registration_status: str | None = None
    gst_hst_number: str | None = None
    provincial_tax_number: str | None = None
    tax_notes: str | None = None
    payment_terms: str | None = None
    workforce_model: str | None = None
    accounting_platform: str | None = None
    typical_services: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Client:
    client_id: str
    business_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Project:
    project_id: str
    business_id: str
    client_id: str | None
    name: str
    description: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Agreement:
    agreement_id: str
    business_id: str
    project_id: str
    title: str
    scope: str
    amount: Decimal | None = None
    currency: str = "CAD"
    status: AgreementStatus = AgreementStatus.DRAFT


@dataclass(frozen=True)
class Estimate:
    estimate_id: str
    business_id: str
    project_id: str
    agreement_id: str | None
    currency: str
    labour_hours_estimate: Decimal | None = None
    labour_rate: Decimal | None = None
    labour_subtotal: Decimal = Decimal("0.00")
    materials_subtotal: Decimal = Decimal("0.00")
    other_subtotal: Decimal = Decimal("0.00")
    total_estimate: Decimal = Decimal("0.00")
    assumptions: str = ""
    status: str = "draft"


@dataclass(frozen=True)
class MaterialPlan:
    material_plan_id: str
    business_id: str
    project_id: str
    agreement_id: str | None
    estimate_id: str | None
    title: str
    notes: str = ""
    approved: bool = False


@dataclass(frozen=True)
class ShoppingListItem:
    shopping_item_id: str
    business_id: str
    project_id: str
    material_plan_id: str
    description: str
    quantity_required: Decimal
    unit: str
    quantity_acquired: Decimal = Decimal("0")
    estimated_unit_cost: Decimal | None = None
    actual_cost: Decimal = Decimal("0.00")
    source_receipt_ids: str = ""
    notes: str = ""

    @property
    def quantity_remaining(self) -> Decimal:
        remaining = self.quantity_required - self.quantity_acquired
        return max(Decimal("0"), remaining)


@dataclass(frozen=True)
class WorkLog:
    work_log_id: str
    business_id: str
    project_id: str
    description: str
    hours: Decimal
    occurred_on: date | None = None
    billable: bool = True
    rate_override: Decimal | None = None


@dataclass(frozen=True)
class ChangeOrder:
    change_order_id: str
    business_id: str
    project_id: str
    agreement_id: str
    title: str
    scope: str
    amount: Decimal | None = None
    currency: str = "CAD"
    status: ChangeOrderStatus = ChangeOrderStatus.DRAFT


@dataclass(frozen=True)
class Expense:
    expense_id: str
    business_id: str
    project_id: str | None
    amount: Decimal
    currency: str
    description: str
    source_goblin: str = "ledgergut"
    source_record_id: str | None = None
    occurred_on: date | None = None
    billable: bool | None = None


@dataclass(frozen=True)
class InvoiceLineItem:
    description: str
    amount: Decimal
    source_type: str
    source_id: str


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    business_id: str
    project_id: str
    client_id: str
    total: Decimal
    currency: str = "CAD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: date | None = None
    agreement_id: str | None = None
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    line_items: tuple[InvoiceLineItem, ...] = ()
    review_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Payment:
    payment_id: str
    business_id: str
    invoice_id: str
    amount: Decimal
    currency: str = "CAD"
    received_on: date | None = None
