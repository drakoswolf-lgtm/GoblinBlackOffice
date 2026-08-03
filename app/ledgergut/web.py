"""Ledgergut minimal web UI — Flask application."""

from __future__ import annotations

import os
import uuid
from datetime import date
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, url_for

from app.ledgergut.form_mapper import build_models
from app.ledgergut.models import BillableStatus, PaidBy, ReimbursementStatus
from app.ledgergut.storage import ReceiptStore, StorageError
from app.ledgergut.validation import validate_receipt

_HERE = Path(__file__).parent
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__, template_folder=str(_HERE / "templates"))
app.secret_key = os.environ.get("LEDGERGUT_SECRET", "ledgergut-dev-secret")

_store = ReceiptStore()


def _enum_options() -> dict:
    return {
        "paid_by": [e.value for e in PaidBy],
        "reimbursement_status": [e.value for e in ReimbursementStatus],
        "billable_status": [e.value for e in BillableStatus],
    }


@app.route("/", methods=["GET"])
def index():
    saved = request.args.get("saved") == "1"
    storage_error = None
    receipts = []
    try:
        receipts = _store.list_receipts()
    except StorageError as exc:
        storage_error = str(exc)
    return render_template(
        "ledgergut/index.html",
        enums=_enum_options(),
        receipts=receipts,
        form_data={},
        findings=[],
        input_errors=[],
        saved=saved,
        storage_error=storage_error,
    )


@app.route("/receipts/new", methods=["POST"])
def new_receipt():
    form_data = request.form.to_dict()

    # Read the uploaded file into memory; do NOT write to disk yet.
    pending_image: tuple[bytes, str] | None = None
    image_file = request.files.get("receipt_image")
    if image_file and image_file.filename:
        ext = image_file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            pending_image = (image_file.read(), ext)

    record, input_errors = build_models(form_data)

    findings = []
    storage_error = None
    if record:
        raw_findings = validate_receipt(record, today=date.today())
        findings = [f.to_dict() for f in raw_findings]
        has_errors = any(f["severity"] == "error" for f in findings)
        if not has_errors and not input_errors:
            # Validation passed — now it is safe to persist the image.
            image_filename = None
            if pending_image is not None:
                image_data, ext = pending_image
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                (_store.image_dir / image_filename).write_bytes(image_data)
            try:
                _store.save_receipt(record.to_dict(), image_filename)
            except StorageError as exc:
                storage_error = str(exc)
            else:
                return redirect(url_for("index") + "?saved=1")

    receipts = []
    try:
        receipts = _store.list_receipts()
    except StorageError as exc:
        storage_error = storage_error or str(exc)
    return render_template(
        "ledgergut/index.html",
        enums=_enum_options(),
        receipts=receipts,
        form_data=form_data,
        findings=findings,
        input_errors=input_errors,
        saved=False,
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
