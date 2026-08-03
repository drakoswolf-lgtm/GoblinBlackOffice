"""Tests for Ledgergut web UI: form mapping, validation, persistence, CSV, routes."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.ledgergut.form_mapper import build_models
from app.ledgergut.storage import CSV_FIELDNAMES, ReceiptStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ReceiptStore:
    return ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )


@pytest.fixture()
def app_client(tmp_path: Path, monkeypatch):
    """Flask test client backed by an isolated temporary store."""
    import app.ledgergut.web as web_module

    store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    monkeypatch.setattr(web_module, "_store", store)
    web_module.app.config["TESTING"] = True
    return web_module.app.test_client(), store


def _valid_form(**overrides) -> dict[str, str]:
    base: dict[str, str] = {
        "vendor_name": "Home Hardware",
        "receipt_date": "2026-07-01",
        "description": "Materials for site",
        "project_name": "Jackson Retail",
        "expense_category": "materials",
        "subtotal": "25.00",
        "tax_amount": "3.00",
        "total_amount": "28.00",
        "currency": "CAD",
        "paid_by": "steve",
        "reimbursement_status": "not_reimbursed",
        "billable_status": "billable",
        "submitted_by": "testuser",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# form_mapper — payload → domain models
# ---------------------------------------------------------------------------


def test_build_models_maps_valid_form_to_receipt_record():
    record, errors = build_models(_valid_form())
    assert errors == []
    assert record is not None
    assert record.receipt.vendor_name == "Home Hardware"
    assert record.receipt.subtotal == Decimal("25.00")
    assert record.receipt.tax_amount == Decimal("3.00")
    assert record.receipt.total_amount == Decimal("28.00")
    assert record.project_name == "Jackson Retail"
    assert record.paid_by.value == "steve"


def test_build_models_uses_cad_default_currency():
    form = _valid_form()
    del form["currency"]
    record, errors = build_models(form)
    assert errors == []
    assert record is not None
    assert record.currency == "CAD"


def test_build_models_malformed_money_yields_user_error():
    form = _valid_form(subtotal="not-a-number")
    record, errors = build_models(form)
    assert record is None
    assert any("Subtotal" in e for e in errors)


def test_build_models_malformed_date_yields_user_error():
    form = _valid_form(receipt_date="07/01/2026")
    record, errors = build_models(form)
    assert record is None
    assert any("date" in e.lower() for e in errors)


def test_build_models_empty_optional_fields_are_none():
    form = _valid_form(project_name="", expense_category="", invoice_id="")
    record, errors = build_models(form)
    assert errors == []
    assert record is not None
    assert record.project_name is None
    assert record.expense_category is None
    assert record.invoice_id is None


def test_build_models_unknown_paid_by_falls_back_to_unknown():
    form = _valid_form(paid_by="gibberish")
    record, errors = build_models(form)
    assert errors == []
    assert record is not None
    assert record.paid_by.value == "unknown"


# ---------------------------------------------------------------------------
# storage — save + reload, missing file init, CSV
# ---------------------------------------------------------------------------


def test_storage_initializes_missing_file(tmp_store: ReceiptStore):
    records = tmp_store.list_receipts()
    assert records == []


def test_storage_save_and_reload(tmp_store: ReceiptStore, tmp_path: Path):
    record, _ = build_models(_valid_form())
    record_id = tmp_store.save_receipt(record.to_dict())  # type: ignore[union-attr]

    store2 = ReceiptStore(
        store_path=tmp_store._path, image_dir=tmp_store._image_dir
    )
    records = store2.list_receipts()
    assert len(records) == 1
    assert records[0]["record_id"] == record_id
    assert records[0]["receipt"]["vendor_name"] == "Home Hardware"


def test_storage_assigns_record_id_when_missing(tmp_store: ReceiptStore):
    record, _ = build_models(_valid_form())
    record_dict = record.to_dict()  # type: ignore[union-attr]
    record_dict.pop("record_id", None)
    record_id = tmp_store.save_receipt(record_dict)
    assert record_id.startswith("LG-")


def test_csv_headers_present(tmp_store: ReceiptStore):
    record, _ = build_models(_valid_form())
    tmp_store.save_receipt(record.to_dict())  # type: ignore[union-attr]
    csv_text = tmp_store.as_csv()
    header_line = csv_text.splitlines()[0]
    for field in CSV_FIELDNAMES:
        assert field in header_line


def test_csv_contains_representative_record(tmp_store: ReceiptStore):
    record, _ = build_models(_valid_form())
    tmp_store.save_receipt(record.to_dict())  # type: ignore[union-attr]
    csv_text = tmp_store.as_csv()
    lines = csv_text.strip().splitlines()
    assert len(lines) == 2  # header + one data row
    assert "Home Hardware" in lines[1]
    assert "2026-07-01" in lines[1]


def test_csv_empty_store_returns_header_only(tmp_store: ReceiptStore):
    csv_text = tmp_store.as_csv()
    lines = [ln for ln in csv_text.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert "record_id" in lines[0]


# ---------------------------------------------------------------------------
# validation findings → UI layer
# ---------------------------------------------------------------------------


def test_validation_findings_surface_for_zero_total():
    """V-03: zero total must surface as an error finding via build_models + validate."""
    from app.ledgergut.validation import validate_receipt

    form = _valid_form(total_amount="0.00")
    record, errors = build_models(form)
    assert errors == []
    findings = validate_receipt(record)  # type: ignore[arg-type]
    rule_ids = [f.rule_id for f in findings]
    assert "V-03" in rule_ids


def test_validation_finding_has_expected_shape():
    from app.ledgergut.validation import validate_receipt

    form = _valid_form(total_amount="0.00")
    record, _ = build_models(form)
    findings = validate_receipt(record)  # type: ignore[arg-type]
    v03 = next(f for f in findings if f.rule_id == "V-03")
    d = v03.to_dict()
    assert d["severity"] == "error"
    assert "total_amount" in d["fields"]
    assert d["message"]


# ---------------------------------------------------------------------------
# Flask route tests
# ---------------------------------------------------------------------------


def test_index_page_loads(app_client):
    client, _ = app_client
    response = client.get("/")
    assert response.status_code == 200
    assert b"Ledgergut" in response.data
    assert b"Save Receipt" in response.data


def test_post_valid_receipt_saves_and_redirects(app_client):
    client, store = app_client
    response = client.post("/receipts/new", data=_valid_form(), follow_redirects=True)
    assert response.status_code == 200
    assert len(store.list_receipts()) == 1
    assert b"saved" in response.data.lower()


def test_post_error_finding_does_not_save(app_client):
    """V-03 (zero total) must block saving and show the finding in HTML."""
    client, store = app_client
    response = client.post("/receipts/new", data=_valid_form(total_amount="0.00"))
    assert response.status_code == 200
    assert b"V-03" in response.data
    assert len(store.list_receipts()) == 0


def test_post_malformed_money_does_not_crash(app_client):
    client, _ = app_client
    response = client.post("/receipts/new", data=_valid_form(subtotal="abc"))
    assert response.status_code == 200
    assert b"Subtotal" in response.data


def test_post_malformed_date_does_not_crash(app_client):
    client, _ = app_client
    response = client.post("/receipts/new", data=_valid_form(receipt_date="not-a-date"))
    assert response.status_code == 200
    assert b"date" in response.data.lower()


def test_csv_export_endpoint(app_client):
    client, store = app_client
    record, _ = build_models(_valid_form())
    store.save_receipt(record.to_dict())  # type: ignore[union-attr]
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert b"record_id" in response.data
    assert b"Home Hardware" in response.data
    assert "text/csv" in response.content_type


def test_csv_export_empty_store(app_client):
    client, _ = app_client
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert b"record_id" in response.data


# ---------------------------------------------------------------------------
# Regression tests for PR review fixes
# ---------------------------------------------------------------------------


def test_rejected_submission_leaves_no_orphaned_image(app_client, tmp_path):
    """Fix 1: image must NOT be written to disk when validation blocks saving."""
    import io

    client, store = app_client

    # V-03 error: zero total blocks saving
    fake_image = (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "receipt.png")
    data = _valid_form(total_amount="0.00")
    response = client.post(
        "/receipts/new",
        data={**data, "receipt_image": fake_image},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"V-03" in response.data
    # The image directory must be empty — no orphaned file
    image_files = list(store.image_dir.iterdir())
    assert image_files == [], f"Unexpected orphaned files: {image_files}"


def test_corrupted_store_raises_storage_error(tmp_store: ReceiptStore):
    """Fix 2: corrupted JSON must raise StorageError and back up the damaged file."""
    from app.ledgergut.storage import StorageError

    tmp_store._path.write_text("{ not valid json {{", encoding="utf-8")
    with pytest.raises(StorageError, match="corrupted"):
        tmp_store.list_receipts()
    # The backup file must exist alongside the store
    backups = list(tmp_store._path.parent.glob("*.corrupted.*.json"))
    assert len(backups) == 1


def test_corrupted_store_does_not_overwrite_data(tmp_store: ReceiptStore):
    """Fix 2: a subsequent save must NOT silently overwrite the damaged store."""
    from app.ledgergut.storage import StorageError

    original_content = "{ not valid json {{"
    tmp_store._path.write_text(original_content, encoding="utf-8")
    with pytest.raises(StorageError):
        tmp_store.save_receipt({"description": "new"})
    # The store file must be unchanged — data not silently overwritten
    assert tmp_store._path.read_text(encoding="utf-8") == original_content


def test_success_banner_appears_after_redirect(app_client):
    """Fix 3: the success banner must be visible when /?saved=1 is loaded."""
    client, _ = app_client
    response = client.get("/?saved=1")
    assert response.status_code == 200
    assert b"saved successfully" in response.data.lower()


def test_success_banner_absent_without_query_param(app_client):
    """Fix 3: the success banner must NOT appear on a plain GET /."""
    client, _ = app_client
    response = client.get("/")
    assert response.status_code == 200
    assert b"saved successfully" not in response.data.lower()


def test_storage_error_on_save_deletes_written_image(app_client):
    """If save_receipt raises StorageError after image write, the image must be deleted."""
    import io

    client, store = app_client

    # Corrupt the store so that save_receipt raises StorageError.
    store._path.parent.mkdir(parents=True, exist_ok=True)
    store._path.write_text("{ corrupted json {{", encoding="utf-8")
    store._image_dir.mkdir(parents=True, exist_ok=True)

    fake_image = (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "receipt.png")
    response = client.post(
        "/receipts/new",
        data={**_valid_form(), "receipt_image": fake_image},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    # The image directory must be empty — the image was rolled back on StorageError.
    image_files = list(store._image_dir.iterdir())
    assert image_files == [], f"Unexpected orphaned files: {image_files}"
