from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from app.models.receipt import Receipt, ReceiptLineItem, ReceiptTaxLine
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate

ROUNDING_TOLERANCE = Decimal("0.05")
KNOWN_PAYERS = {"steve", "company_card", "client_card", "rob_visa", "cash"}


def _money(value: Decimal | float | int | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalize_project(name: str | None) -> str | None:
    if name is None:
        return None
    trimmed = name.strip()
    return trimmed or None


def _append_note(notes: list[str], message: str) -> None:
    if message not in notes:
        notes.append(message)


def _validate_receipt_fields(payload: ReceiptCreate | ReceiptUpdate) -> tuple[bool, str | None, str]:
    needs_review = bool(payload.needs_user_review)
    notes: list[str] = []

    subtotal = _money(payload.subtotal)
    tax_amount = _money(payload.tax_amount)
    printed_total_amount = _money(payload.printed_total_amount)
    actual_paid_amount = _money(payload.actual_paid_amount)
    cash_rounding_adjustment = _money(payload.cash_rounding_adjustment) or Decimal("0.00")
    cash_tendered = _money(payload.cash_tendered)
    change_due = _money(payload.change_due)
    payment_method = (payload.payment_method or "").lower()
    project_name = _normalize_project(payload.project_name)
    project_name_raw = _normalize_project(payload.project_name_raw)
    paid_by = _normalize_project(payload.paid_by)

    if subtotal is not None and tax_amount is not None and printed_total_amount is not None:
        expected_total = subtotal + tax_amount
        if abs(expected_total - printed_total_amount) > ROUNDING_TOLERANCE:
            needs_review = True
            _append_note(notes, "Printed total does not match subtotal plus tax within rounding tolerance.")

    if printed_total_amount is not None and change_due is not None and printed_total_amount == change_due:
        needs_review = True
        _append_note(notes, "Change due matches the printed total; confirm total was captured correctly.")

    if actual_paid_amount is not None and printed_total_amount is not None and payment_method == "cash":
        expected_paid = printed_total_amount + cash_rounding_adjustment
        if abs(expected_paid - actual_paid_amount) > ROUNDING_TOLERANCE:
            needs_review = True
            _append_note(notes, "Cash rounding and actual paid amount are inconsistent.")

    if cash_tendered is not None and actual_paid_amount is not None and change_due is not None:
        expected_change = cash_tendered - actual_paid_amount
        if abs(expected_change - change_due) > ROUNDING_TOLERANCE:
            needs_review = True
            _append_note(notes, "Cash tendered, actual paid amount, and change due are inconsistent.")

    if project_name_raw and project_name and project_name_raw != project_name:
        needs_review = True
        _append_note(notes, f"Project name appears as {project_name_raw} and was normalized to {project_name}.")

    if not project_name:
        needs_review = True
        _append_note(notes, "Project name is missing and requires human review before invoicing.")

    if not paid_by or paid_by.lower() not in KNOWN_PAYERS:
        needs_review = True
        _append_note(notes, "Paid by is missing or unknown and requires human review.")

    if payload.receipt_date and payload.receipt_date > date.today():
        raise HTTPException(status_code=422, detail="receipt_date cannot be in the future")

    status = payload.status.value if payload.status else ("pending_review" if needs_review else "approved")
    review_notes = " ".join(notes) if notes else payload.review_notes
    return needs_review, review_notes, status


def _build_receipt_model(record_id: str, payload: ReceiptCreate | ReceiptUpdate) -> Receipt:
    needs_review, review_notes, status = _validate_receipt_fields(payload)
    receipt = Receipt(
        record_id=record_id,
        vendor_name=payload.vendor_name,
        vendor_location=payload.vendor_location,
        receipt_date=payload.receipt_date,
        receipt_time=payload.receipt_time,
        receipt_date_raw=payload.receipt_date_raw,
        transaction_id=payload.transaction_id,
        project_name_raw=_normalize_project(payload.project_name_raw),
        project_name=_normalize_project(payload.project_name),
        project_confidence=payload.project_confidence,
        paid_by=_normalize_project(payload.paid_by),
        payment_method=payload.payment_method,
        expense_category=payload.expense_category,
        subtotal=_money(payload.subtotal),
        tax_amount=_money(payload.tax_amount),
        printed_total_amount=_money(payload.printed_total_amount),
        cash_rounding_adjustment=_money(payload.cash_rounding_adjustment),
        actual_paid_amount=_money(payload.actual_paid_amount),
        cash_tendered=_money(payload.cash_tendered),
        change_due=_money(payload.change_due),
        currency=payload.currency or "CAD",
        tax_region=payload.tax_region or "BC",
        billable_status=payload.billable_status.value if payload.billable_status else None,
        reimbursement_status=payload.reimbursement_status.value if payload.reimbursement_status else None,
        invoice_id=payload.invoice_id,
        status=status,
        needs_user_review=needs_review,
        review_notes=review_notes,
    )
    receipt.line_items = [
        ReceiptLineItem(
            record_id=record_id,
            sku=item.sku,
            description=item.description,
            quantity=_money(item.quantity),
            unit_price=_money(item.unit_price),
            amount=_money(item.amount),
            notes=item.notes,
        )
        for item in payload.line_items
    ]
    receipt.tax_lines = [
        ReceiptTaxLine(
            record_id=record_id,
            label=tax_line.label,
            rate=tax_line.rate,
            amount=_money(tax_line.amount),
        )
        for tax_line in payload.tax_lines
    ]
    return receipt


def _receipt_query(db: Session):
    return db.query(Receipt).options(
        selectinload(Receipt.line_items),
        selectinload(Receipt.tax_lines),
    )


def generate_receipt_id() -> str:
    return f"LG-{datetime.utcnow():%Y%m%d}-{uuid4().hex[:8].upper()}"


def seed_sample_receipts(db: Session) -> None:
    if db.query(Receipt).count():
        return

    sample_receipts = [
        ReceiptCreate(
            vendor_name="Home Depot",
            vendor_location="900 Terminal Avenue, Vancouver, BC",
            receipt_date=date(2026, 7, 3),
            receipt_time=time(20, 41),
            project_name_raw="SKYLIGT",
            project_name="Skylight",
            project_confidence=Decimal("0.86"),
            paid_by="steve",
            payment_method="cash",
            expense_category="materials",
            subtotal=Decimal("49.18"),
            tax_amount=Decimal("5.90"),
            printed_total_amount=Decimal("55.08"),
            cash_rounding_adjustment=Decimal("-0.03"),
            actual_paid_amount=Decimal("55.05"),
            cash_tendered=Decimal("100.00"),
            change_due=Decimal("44.95"),
            currency="CAD",
            tax_region="BC",
            billable_status="maybe_billable",
            reimbursement_status="not_reimbursed",
            needs_user_review=True,
            review_notes="Project name appears as SKYLIGT and was normalized to Skylight. Confirm project and billability.",
            line_items=[
                {
                    "sku": "066366153880",
                    "description": "Pulleys",
                    "quantity": Decimal("2"),
                    "unit_price": Decimal("14.23"),
                    "amount": Decimal("28.46"),
                },
                {
                    "sku": "066365630152",
                    "description": "Pulleys",
                    "quantity": Decimal("2"),
                    "unit_price": Decimal("10.36"),
                    "amount": Decimal("20.72"),
                },
            ],
            tax_lines=[
                {"label": "GST/HST", "rate": Decimal("0.05"), "amount": Decimal("2.46")},
                {"label": "PST/QST", "rate": Decimal("0.07"), "amount": Decimal("3.44")},
            ],
        ),
        ReceiptCreate(
            vendor_name="Canadian Tire #604",
            vendor_location="2830 Bentall St, Vancouver, BC",
            receipt_date=date(2026, 7, 3),
            receipt_time=time(21, 15, 58),
            transaction_id="160",
            paid_by="steve",
            payment_method="cash",
            expense_category="materials",
            subtotal=Decimal("48.99"),
            tax_amount=Decimal("5.88"),
            printed_total_amount=Decimal("54.87"),
            cash_rounding_adjustment=Decimal("-0.02"),
            actual_paid_amount=Decimal("54.85"),
            cash_tendered=Decimal("100.00"),
            change_due=Decimal("45.15"),
            currency="CAD",
            tax_region="BC",
            billable_status="maybe_billable",
            reimbursement_status="not_reimbursed",
            needs_user_review=True,
            review_notes="No project/job name printed. Human must confirm project before invoicing.",
            line_items=[
                {
                    "sku": "040-6944-2",
                    "description": "MM Trailer Winch",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("39.99"),
                    "amount": Decimal("39.99"),
                },
                {
                    "sku": "199-2930-2",
                    "description": "As-is item",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("9.00"),
                    "amount": Decimal("9.00"),
                    "notes": "Final sale. Original product number appears to be 073-5405-4.",
                },
            ],
            tax_lines=[
                {"label": "GST", "rate": Decimal("0.05"), "amount": Decimal("2.45")},
                {"label": "PST", "rate": Decimal("0.07"), "amount": Decimal("3.43")},
            ],
        ),
    ]

    seeded = [
        _build_receipt_model("LG-20260703-0001", sample_receipts[0]),
        _build_receipt_model("LG-20260703-0002", sample_receipts[1]),
    ]
    db.add_all(seeded)
    db.commit()


def create_receipt(db: Session, payload: ReceiptCreate) -> Receipt:
    receipt = _build_receipt_model(generate_receipt_id(), payload)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return get_receipt_or_404(db, receipt.record_id)


def list_receipts(db: Session) -> list[Receipt]:
    return _receipt_query(db).order_by(Receipt.created_at.asc()).all()


def get_receipt_or_404(db: Session, record_id: str) -> Receipt:
    receipt = _receipt_query(db).filter(Receipt.record_id == record_id).first()
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


def update_receipt(db: Session, record_id: str, payload: ReceiptUpdate) -> Receipt:
    receipt = get_receipt_or_404(db, record_id)

    update_data = payload.model_dump(exclude_unset=True)
    line_items = update_data.pop("line_items", None)
    tax_lines = update_data.pop("tax_lines", None)

    merged_data = {
        "vendor_name": update_data.get("vendor_name", receipt.vendor_name),
        "vendor_location": update_data.get("vendor_location", receipt.vendor_location),
        "receipt_date": update_data.get("receipt_date", receipt.receipt_date),
        "receipt_time": update_data.get("receipt_time", receipt.receipt_time),
        "receipt_date_raw": update_data.get("receipt_date_raw", receipt.receipt_date_raw),
        "transaction_id": update_data.get("transaction_id", receipt.transaction_id),
        "project_name_raw": update_data.get("project_name_raw", receipt.project_name_raw),
        "project_name": update_data.get("project_name", receipt.project_name),
        "project_confidence": update_data.get("project_confidence", receipt.project_confidence),
        "paid_by": update_data.get("paid_by", receipt.paid_by),
        "payment_method": update_data.get("payment_method", receipt.payment_method),
        "expense_category": update_data.get("expense_category", receipt.expense_category),
        "subtotal": update_data.get("subtotal", receipt.subtotal),
        "tax_amount": update_data.get("tax_amount", receipt.tax_amount),
        "printed_total_amount": update_data.get("printed_total_amount", receipt.printed_total_amount),
        "cash_rounding_adjustment": update_data.get("cash_rounding_adjustment", receipt.cash_rounding_adjustment),
        "actual_paid_amount": update_data.get("actual_paid_amount", receipt.actual_paid_amount),
        "cash_tendered": update_data.get("cash_tendered", receipt.cash_tendered),
        "change_due": update_data.get("change_due", receipt.change_due),
        "currency": update_data.get("currency", receipt.currency),
        "tax_region": update_data.get("tax_region", receipt.tax_region),
        "billable_status": update_data.get("billable_status", receipt.billable_status),
        "reimbursement_status": update_data.get("reimbursement_status", receipt.reimbursement_status),
        "invoice_id": update_data.get("invoice_id", receipt.invoice_id),
        "status": update_data.get("status", receipt.status),
        "needs_user_review": update_data.get("needs_user_review", receipt.needs_user_review),
        "review_notes": update_data.get("review_notes", receipt.review_notes),
        "line_items": line_items
        if line_items is not None
        else [
            {
                "sku": item.sku,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
                "notes": item.notes,
            }
            for item in receipt.line_items
        ],
        "tax_lines": tax_lines
        if tax_lines is not None
        else [
            {"label": tax_line.label, "rate": tax_line.rate, "amount": tax_line.amount}
            for tax_line in receipt.tax_lines
        ],
    }

    normalized_payload = ReceiptCreate.model_validate(merged_data)
    refreshed = _build_receipt_model(record_id, normalized_payload)

    for field in [
        "vendor_name",
        "vendor_location",
        "receipt_date",
        "receipt_time",
        "receipt_date_raw",
        "transaction_id",
        "project_name_raw",
        "project_name",
        "project_confidence",
        "paid_by",
        "payment_method",
        "expense_category",
        "subtotal",
        "tax_amount",
        "printed_total_amount",
        "cash_rounding_adjustment",
        "actual_paid_amount",
        "cash_tendered",
        "change_due",
        "currency",
        "tax_region",
        "billable_status",
        "reimbursement_status",
        "invoice_id",
        "status",
        "needs_user_review",
        "review_notes",
    ]:
        setattr(receipt, field, getattr(refreshed, field))

    receipt.line_items.clear()
    receipt.line_items.extend(refreshed.line_items)
    receipt.tax_lines.clear()
    receipt.tax_lines.extend(refreshed.tax_lines)

    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return get_receipt_or_404(db, record_id)
