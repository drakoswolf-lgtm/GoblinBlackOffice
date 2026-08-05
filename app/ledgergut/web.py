"""Ledgergut minimal web UI — Flask application."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, url_for

from app.ledgergut.form_mapper import build_models
from app.ledgergut.models import BillableStatus, PaidBy, ReimbursementStatus
from app.ledgergut.ocr import OcrError, extract_text_from_image
from app.ledgergut.receipt_parser import ReceiptSuggestions, parse_receipt_text
from app.ledgergut.storage import ReceiptStore, StorageError
from app.ledgergut.validation import validate_receipt

_HERE = Path(__file__).parent
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PENDING_IMAGE_TTL = timedelta(minutes=30)

app = Flask(__name__, template_folder=str(_HERE / "templates"))
app.secret_key = os.environ.get("LEDGERGUT_SECRET", "ledgergut-dev-secret")

_store = ReceiptStore()


def _enum_options() -> dict:
    return {
        "paid_by": [e.value for e in PaidBy],
        "reimbursement_status": [e.value for e in ReimbursementStatus],
        "billable_status": [e.value for e in BillableStatus],
    }


def _ocr_notes_from_form(form_data: dict[str, str]) -> list[str]:
    return [line for line in form_data.get("ocr_confidence_notes", "").splitlines() if line.strip()]


def _pending_images() -> dict[str, dict[str, str]]:
    pending_images = app.config.setdefault("LEDGERGUT_PENDING_IMAGES", {})
    assert isinstance(pending_images, dict)
    return pending_images


def _prune_pending_images(now: datetime | None = None) -> None:
    current_time = now or datetime.now(timezone.utc)
    expired_tokens = []
    for token, payload in _pending_images().items():
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if expires_at <= current_time:
            expired_tokens.append(token)
    for token in expired_tokens:
        _pending_images().pop(token, None)


def _store_pending_image(image_data: bytes, ext: str) -> str:
    _prune_pending_images()
    token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + PENDING_IMAGE_TTL
    _pending_images()[token] = {
        "image_data": image_data.hex(),
        "ext": ext,
        "expires_at": expires_at.isoformat(),
    }
    return token


def _consume_pending_image(token: str) -> tuple[bytes, str] | None:
    _prune_pending_images()
    payload = _pending_images().pop(token, None)
    if payload is None:
        return None
    return bytes.fromhex(payload["image_data"]), payload["ext"]


def _render_index(
    *,
    form_data: dict[str, str] | None = None,
    findings: list[dict] | None = None,
    input_errors: list[str] | None = None,
    saved: bool = False,
    storage_error: str | None = None,
    scan_message: str | None = None,
    scan_error: str | None = None,
) -> str:
    receipts = []
    try:
        receipts = _store.list_receipts()
    except StorageError as exc:
        storage_error = storage_error or str(exc)

    page_form_data = form_data or {}
    return render_template(
        "ledgergut/index.html",
        enums=_enum_options(),
        receipts=receipts,
        form_data=page_form_data,
        findings=findings or [],
        input_errors=input_errors or [],
        saved=saved,
        storage_error=storage_error,
        scan_message=scan_message,
        scan_error=scan_error,
        ocr_raw_text=page_form_data.get("ocr_raw_text", ""),
        ocr_confidence_notes=_ocr_notes_from_form(page_form_data),
    )


def _read_pending_image(*, required: bool) -> tuple[tuple[bytes, str] | None, str | None]:
    image_file = request.files.get("receipt_image")
    if image_file is None or not image_file.filename:
        if required:
            return None, "Upload a PNG or JPG receipt image under 10 MB to scan."
        return None, None

    ext = image_file.filename.rsplit(".", 1)[-1].lower() if "." in image_file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, "Unsupported receipt image. Upload a PNG or JPG file under 10 MB."

    image_data = image_file.read()
    if not image_data:
        return None, "Receipt image was empty. Upload a PNG or JPG file under 10 MB."
    if len(image_data) > MAX_UPLOAD_BYTES:
        return None, "Receipt image is too large. Upload a PNG or JPG file under 10 MB."
    return (image_data, ext), None


def _apply_suggestions(form_data: dict[str, str], suggestions: ReceiptSuggestions) -> dict[str, str]:
    updated = dict(form_data)
    if suggestions.vendor_name is not None and not updated.get("vendor_name", "").strip():
        updated["vendor_name"] = suggestions.vendor_name
    if suggestions.receipt_date is not None and not updated.get("receipt_date", "").strip():
        updated["receipt_date"] = suggestions.receipt_date.isoformat()
    if suggestions.subtotal is not None and not updated.get("subtotal", "").strip():
        updated["subtotal"] = f"{suggestions.subtotal:.2f}"
    if suggestions.tax_amount is not None and not updated.get("tax_amount", "").strip():
        updated["tax_amount"] = f"{suggestions.tax_amount:.2f}"
    if suggestions.total_amount is not None and not updated.get("total_amount", "").strip():
        updated["total_amount"] = f"{suggestions.total_amount:.2f}"
    if suggestions.receipt_number is not None and not updated.get("receipt_number", "").strip():
        updated["receipt_number"] = suggestions.receipt_number
    updated["ocr_raw_text"] = suggestions.raw_text
    updated["ocr_confidence_notes"] = "\n".join(suggestions.confidence_notes)
    return updated


@app.route("/", methods=["GET"])
def index():
    return _render_index(saved=request.args.get("saved") == "1")


@app.route("/receipts/scan", methods=["POST"])
def scan_receipt():
    form_data = request.form.to_dict()
    pending_image, image_error = _read_pending_image(required=True)
    if image_error is not None:
        return _render_index(
            form_data=form_data,
            scan_error=image_error,
        )

    assert pending_image is not None
    image_data, ext = pending_image
    try:
        raw_text = extract_text_from_image(image_data)
        suggestions = parse_receipt_text(raw_text)
    except OcrError as exc:
        return _render_index(
            form_data=form_data,
            scan_error=str(exc),
        )

    updated_form_data = _apply_suggestions(form_data, suggestions)
    updated_form_data["pending_image_token"] = _store_pending_image(image_data, ext)
    return _render_index(
        form_data=updated_form_data,
        scan_message="OCR suggestions loaded. Review every extracted field before saving.",
    )


@app.route("/receipts/new", methods=["POST"])
def new_receipt():
    form_data = request.form.to_dict()

    # Read the uploaded file into memory; do NOT write to disk yet.
    pending_image, image_error = _read_pending_image(required=False)
    if pending_image is None:
        pending_image_token = form_data.get("pending_image_token", "").strip()
        if pending_image_token:
            pending_image = _consume_pending_image(pending_image_token)
            if pending_image is None:
                input_error = "Scanned receipt image expired. Re-upload the image before saving."
                image_error = input_error if image_error is None else image_error
    record, input_errors = build_models(form_data)
    if image_error:
        input_errors.append(image_error)

    findings = []
    storage_error = None
    if record:
        raw_findings = validate_receipt(record, today=date.today())
        findings = [f.to_dict() for f in raw_findings]
        has_errors = any(f["severity"] == "error" for f in findings)
        if not has_errors and not input_errors:
            # Validation passed — now it is safe to persist the image.
            image_filename = None
            written_image_path: Path | None = None
            if pending_image is not None:
                image_data, ext = pending_image
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                written_image_path = _store.image_dir / image_filename
                written_image_path.write_bytes(image_data)
            try:
                _store.save_receipt(record.to_dict(), image_filename)
            except StorageError as exc:
                # Roll back: remove the image that was just written so it does
                # not remain on disk without a corresponding receipt record.
                if written_image_path is not None:
                    written_image_path.unlink(missing_ok=True)
                storage_error = str(exc)
            else:
                return redirect(url_for("index") + "?saved=1")

    return _render_index(
        form_data=form_data,
        findings=findings,
        input_errors=input_errors,
        storage_error=storage_error,
    )


@app.route("/export/csv")
def export_csv():
    try:
        csv_data = _store.as_csv()
    except StorageError:
        return Response(
            "Receipt store is unavailable. Check the server console for details.",
            status=500,
            mimetype="text/plain",
        )
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ledgergut-receipts.csv"},
    )
