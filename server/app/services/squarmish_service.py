from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.models.invoice import InvoiceDraft, InvoiceLineItem
from app.models.receipt import Receipt

ELIGIBLE_BILLABLE_STATUSES = {"billable", "maybe_billable", "tax_only"}

PROJECT_CLIENT_MAP = {}
TAX_RATES = {
    "gst_only": Decimal("0.05"),
    "gst_pst": Decimal("0.12"),
    "hst": Decimal("0.13"),
    "gst_qst": Decimal("0.14975"),
    "exempt": Decimal("0.00"),
    "non_taxable": Decimal("0.00"),
    "tax_passthrough": Decimal("0.00"),
    "needs_review": Decimal("0.00"),
}


def _money(value: Decimal | float | int | str | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _invoice_query(db: Session):
    return db.query(InvoiceDraft).options(selectinload(InvoiceDraft.line_items))


def _generate_invoice_id() -> str:
    return f"SQ-{date.today():%Y%m%d}-{uuid4().hex[:8].upper()}"


def _default_tax_treatment(receipt: Receipt) -> str:
    if receipt.billable_status == "tax_only":
        return "tax_passthrough"
    if (receipt.tax_region or "").upper() == "BC":
        return "gst_pst"
    return "needs_review"


def _receipt_review_reasons(receipt: Receipt) -> list[str]:
    reasons: list[str] = []
    if receipt.billable_status == "maybe_billable":
        reasons.append(f"{receipt.record_id} is marked maybe_billable.")
    if receipt.billable_status == "tax_only":
        reasons.append(f"{receipt.record_id} is marked tax_only.")
    if receipt.project_name_raw and receipt.project_name and receipt.project_name_raw != receipt.project_name:
        reasons.append(f"{receipt.record_id} project was normalized from raw receipt text.")
    if receipt.needs_user_review:
        reasons.append(f"{receipt.record_id} already requires Ledgergut review.")
    if receipt.review_notes and "inconsistent" in receipt.review_notes.lower():
        reasons.append(f"{receipt.record_id} has payment or rounding inconsistencies.")
    return reasons


def _build_line_items(receipt: Receipt) -> list[InvoiceLineItem]:
    tax_treatment = _default_tax_treatment(receipt)
    review_status = "needs_review" if receipt.billable_status in {"maybe_billable", "tax_only"} or tax_treatment == "needs_review" else "confirmed"
    line_item_type = "tax_passthrough" if receipt.billable_status == "tax_only" else "materials"
    taxable = tax_treatment not in {"non_taxable", "exempt", "tax_passthrough"}
    tax_notes = "Preserved receipt tax lines: " + ", ".join(
        f"{tax_line.label}={_money(tax_line.amount)}" for tax_line in receipt.tax_lines
    ) if receipt.tax_lines else None

    if receipt.line_items:
        return [
            InvoiceLineItem(
                description=f"{receipt.vendor_name or 'Unknown vendor'} — {item.description}",
                quantity=item.quantity,
                unit="item",
                unit_price=item.unit_price,
                amount=item.amount,
                line_item_type=line_item_type,
                linked_record_id=receipt.record_id,
                billable_status=receipt.billable_status,
                taxable=taxable,
                tax_treatment=tax_treatment,
                tax_region=receipt.tax_region,
                tax_notes=tax_notes,
                review_status=review_status,
            )
            for item in receipt.line_items
        ]

    fallback_amount = receipt.subtotal if receipt.subtotal is not None else receipt.printed_total_amount
    return [
        InvoiceLineItem(
            description=f"{receipt.vendor_name or 'Unknown vendor'} materials",
            quantity=Decimal("1.00"),
            unit="receipt",
            unit_price=_money(fallback_amount),
            amount=_money(fallback_amount),
            line_item_type=line_item_type,
            linked_record_id=receipt.record_id,
            billable_status=receipt.billable_status,
            taxable=taxable,
            tax_treatment=tax_treatment,
            tax_region=receipt.tax_region,
            tax_notes=tax_notes or "Fallback materials line created from receipt subtotal/total.",
            review_status=review_status,
        )
    ]


def create_invoice_from_project(db: Session, project_name: str) -> InvoiceDraft:
    receipts = (
        db.query(Receipt)
        .options(selectinload(Receipt.line_items), selectinload(Receipt.tax_lines))
        .filter(Receipt.project_name == project_name)
        .filter(Receipt.billable_status.in_(ELIGIBLE_BILLABLE_STATUSES))
        .filter(Receipt.invoice_id.is_(None))
        .order_by(Receipt.receipt_date.asc(), Receipt.created_at.asc())
        .all()
    )

    if not receipts:
        raise HTTPException(status_code=404, detail="No billable receipts found for project")

    client_name = PROJECT_CLIENT_MAP.get(project_name)
    review_notes: list[str] = []
    if not client_name:
        review_notes.append("Client name is missing for this project.")

    line_items: list[InvoiceLineItem] = []
    for receipt in receipts:
        line_items.extend(_build_line_items(receipt))
        review_notes.extend(_receipt_review_reasons(receipt))

    subtotal = sum((_money(line_item.amount) for line_item in line_items), Decimal("0.00"))
    tax_amount = Decimal("0.00")
    for line_item in line_items:
        rate = TAX_RATES.get(line_item.tax_treatment, Decimal("0.00"))
        tax_amount += _money(line_item.amount) * rate
    tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    printed_total_amount = sum((_money(receipt.printed_total_amount) for receipt in receipts), Decimal("0.00"))
    actual_paid_amount = sum((_money(receipt.actual_paid_amount) for receipt in receipts), Decimal("0.00"))
    needs_user_review = bool(review_notes) or any(
        line_item.review_status == "needs_review" for line_item in line_items
    )
    if any(line_item.tax_treatment == "needs_review" for line_item in line_items):
        review_notes.append("Tax treatment is uncertain for at least one line item.")

    invoice = InvoiceDraft(
        invoice_id=_generate_invoice_id(),
        client_name=client_name,
        project_name=project_name,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        currency=receipts[0].currency or "CAD",
        tax_region=receipts[0].tax_region or "BC",
        subtotal=subtotal,
        tax_amount=tax_amount,
        printed_total_amount=printed_total_amount,
        actual_paid_amount=actual_paid_amount,
        status="pending_review" if needs_user_review else "draft",
        needs_user_review=needs_user_review,
        review_notes=" ".join(dict.fromkeys(review_notes)) or None,
        line_items=line_items,
    )
    db.add(invoice)
    for receipt in receipts:
        receipt.invoice_id = invoice.invoice_id
        if receipt.billable_status in {"billable", "maybe_billable", "tax_only"}:
            receipt.status = "partial_approval" if receipt.needs_user_review else receipt.status
    db.commit()
    db.refresh(invoice)
    return get_invoice_or_404(db, invoice.invoice_id)


def list_invoices(db: Session) -> list[InvoiceDraft]:
    return _invoice_query(db).order_by(InvoiceDraft.created_at.asc()).all()


def get_invoice_or_404(db: Session, invoice_id: str) -> InvoiceDraft:
    invoice = _invoice_query(db).filter(InvoiceDraft.invoice_id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
