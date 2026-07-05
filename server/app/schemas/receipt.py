from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel, ReceiptCoreFields, ReceiptLineItemBase, ReceiptTaxLineBase


class ReceiptCreate(ReceiptCoreFields):
    line_items: list[ReceiptLineItemBase] = Field(default_factory=list)
    tax_lines: list[ReceiptTaxLineBase] = Field(default_factory=list)


class ReceiptUpdate(ReceiptCoreFields):
    line_items: list[ReceiptLineItemBase] | None = None
    tax_lines: list[ReceiptTaxLineBase] | None = None


class ReceiptLineItemRead(ReceiptLineItemBase):
    record_id: str


class ReceiptTaxLineRead(ReceiptTaxLineBase):
    record_id: str


class ReceiptRead(ReceiptCoreFields):
    record_id: str
    created_at: datetime
    updated_at: datetime
    line_items: list[ReceiptLineItemRead]
    tax_lines: list[ReceiptTaxLineRead]


class ReceiptListResponse(ORMModel):
    receipts: list[ReceiptRead]
