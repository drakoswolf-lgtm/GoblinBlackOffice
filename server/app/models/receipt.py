from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Receipt(Base):
    __tablename__ = "receipts"

    record_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255))
    vendor_location: Mapped[str | None] = mapped_column(String(255))
    receipt_date: Mapped[date | None] = mapped_column(Date)
    receipt_time: Mapped[time | None] = mapped_column(Time)
    receipt_date_raw: Mapped[str | None] = mapped_column(String(255))
    transaction_id: Mapped[str | None] = mapped_column(String(255))
    project_name_raw: Mapped[str | None] = mapped_column(String(255))
    project_name: Mapped[str | None] = mapped_column(String(255))
    project_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    paid_by: Mapped[str | None] = mapped_column(String(50))
    payment_method: Mapped[str | None] = mapped_column(String(50))
    expense_category: Mapped[str | None] = mapped_column(String(100))
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    printed_total_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    cash_rounding_adjustment: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    actual_paid_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    cash_tendered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    change_due: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    tax_region: Mapped[str | None] = mapped_column(String(20))
    billable_status: Mapped[str | None] = mapped_column(String(50))
    reimbursement_status: Mapped[str | None] = mapped_column(String(50))
    invoice_id: Mapped[str | None] = mapped_column(ForeignKey("invoice_drafts.invoice_id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending_review")
    needs_user_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    line_items: Mapped[list["ReceiptLineItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="ReceiptLineItem.id",
    )
    tax_lines: Mapped[list["ReceiptTaxLine"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="ReceiptTaxLine.id",
    )


class ReceiptLineItem(Base):
    __tablename__ = "receipt_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(ForeignKey("receipts.record_id"), index=True)
    sku: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    receipt: Mapped["Receipt"] = relationship(back_populates="line_items")


class ReceiptTaxLine(Base):
    __tablename__ = "receipt_tax_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(ForeignKey("receipts.record_id"), index=True)
    label: Mapped[str] = mapped_column(String(100))
    rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    receipt: Mapped["Receipt"] = relationship(back_populates="tax_lines")
