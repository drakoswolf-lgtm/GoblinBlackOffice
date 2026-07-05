from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class InvoiceDraft(Base):
    __tablename__ = "invoice_drafts"

    invoice_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    client_name: Mapped[str | None] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(255), index=True)
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(10))
    tax_region: Mapped[str | None] = mapped_column(String(20))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    printed_total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    actual_paid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    needs_user_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLineItem.id",
    )


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoice_drafts.invoice_id"), index=True)
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit: Mapped[str] = mapped_column(String(50))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    line_item_type: Mapped[str] = mapped_column(String(50))
    linked_record_id: Mapped[str | None] = mapped_column(ForeignKey("receipts.record_id"), index=True)
    billable_status: Mapped[str | None] = mapped_column(String(50))
    taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_treatment: Mapped[str] = mapped_column(String(50))
    tax_region: Mapped[str | None] = mapped_column(String(20))
    tax_notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(50), default="needs_review")

    invoice: Mapped["InvoiceDraft"] = relationship(back_populates="line_items")
