from __future__ import annotations

from app.schemas.common import InvoiceCoreFields, InvoiceLineItemBase, ORMModel


class InvoiceLineItemRead(InvoiceLineItemBase):
    invoice_id: str


class InvoiceRead(InvoiceCoreFields):
    invoice_id: str
    line_items: list[InvoiceLineItemRead]


class InvoiceListResponse(ORMModel):
    invoices: list[InvoiceRead]
