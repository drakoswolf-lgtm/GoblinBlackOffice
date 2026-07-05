from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BillableStatus(str, Enum):
    billable = "billable"
    maybe_billable = "maybe_billable"
    not_billable = "not_billable"
    already_invoiced = "already_invoiced"
    tax_only = "tax_only"


class ReimbursementStatus(str, Enum):
    not_reimbursed = "not_reimbursed"
    reimbursed = "reimbursed"
    maybe_reimbursed = "maybe_reimbursed"
    not_reimbursable = "not_reimbursable"
    unknown = "unknown"


class ReceiptStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    partial_approval = "partial_approval"


class InvoiceStatus(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    issued = "issued"
    paid = "paid"
    partially_paid = "partially_paid"
    overdue = "overdue"
    voided = "voided"


class TaxTreatment(str, Enum):
    gst_only = "gst_only"
    gst_pst = "gst_pst"
    hst = "hst"
    gst_qst = "gst_qst"
    exempt = "exempt"
    non_taxable = "non_taxable"
    tax_passthrough = "tax_passthrough"
    needs_review = "needs_review"


class LineItemType(str, Enum):
    materials = "materials"
    labour = "labour"
    subcontractor = "subcontractor"
    fee = "fee"
    travel = "travel"
    tax_passthrough = "tax_passthrough"
    discount = "discount"
    other = "other"


class ReviewStatus(str, Enum):
    confirmed = "confirmed"
    needs_review = "needs_review"
    auto_approved = "auto_approved"
    rejected = "rejected"


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReceiptLineItemBase(ORMModel):
    sku: str | None = None
    description: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal
    amount: Decimal
    notes: str | None = None


class ReceiptTaxLineBase(ORMModel):
    label: str
    rate: Decimal | None = None
    amount: Decimal


class ReceiptCoreFields(ORMModel):
    vendor_name: str | None = None
    vendor_location: str | None = None
    receipt_date: date | None = None
    receipt_time: time | None = None
    receipt_date_raw: str | None = None
    transaction_id: str | None = None
    project_name_raw: str | None = None
    project_name: str | None = None
    project_confidence: Decimal | None = None
    paid_by: str | None = None
    payment_method: str | None = None
    expense_category: str | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    printed_total_amount: Decimal | None = None
    cash_rounding_adjustment: Decimal | None = None
    actual_paid_amount: Decimal | None = None
    cash_tendered: Decimal | None = None
    change_due: Decimal | None = None
    currency: str | None = None
    tax_region: str | None = None
    billable_status: BillableStatus | None = None
    reimbursement_status: ReimbursementStatus | None = None
    invoice_id: str | None = None
    status: ReceiptStatus | None = None
    needs_user_review: bool | None = None
    review_notes: str | None = None


class InvoiceLineItemBase(ORMModel):
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    amount: Decimal
    line_item_type: LineItemType
    linked_record_id: str | None = None
    billable_status: BillableStatus | None = None
    taxable: bool
    tax_treatment: TaxTreatment
    tax_region: str | None = None
    tax_notes: str | None = None
    review_status: ReviewStatus


class InvoiceCoreFields(ORMModel):
    client_name: str | None = None
    project_name: str
    invoice_date: date
    due_date: date
    currency: str | None = None
    tax_region: str | None = None
    subtotal: Decimal
    tax_amount: Decimal
    printed_total_amount: Decimal
    actual_paid_amount: Decimal
    status: InvoiceStatus
    needs_user_review: bool
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime
