from pathlib import Path

from app.ledgergut.image_store import (
    LocalReceiptImageStore,
    ReceiptImageStoreError,
    S3ReceiptImageStore,
)
from app.ledgergut.storage import ReceiptStore


def test_local_image_store_get_round_trip_and_blocks_paths(tmp_path: Path):
    store = LocalReceiptImageStore(tmp_path)
    key = store.put(
        business_id="BIZ-A",
        filename="receipt.jpg",
        data=b"receipt-image",
        content_type="image/jpeg",
    )

    data, content_type = store.get(business_id="BIZ-A", key=key)
    assert data == b"receipt-image"
    assert content_type == "image/jpeg"

    try:
        store.get(business_id="BIZ-A", key="../receipt.jpg")
    except ReceiptImageStoreError:
        pass
    else:
        raise AssertionError("Local image retrieval accepted a path traversal key.")


def test_spaces_image_store_rejects_cross_business_key_before_network():
    store = object.__new__(S3ReceiptImageStore)
    store.bucket = "private-receipts"
    store.client = None

    try:
        store.get(business_id="BIZ-A", key="receipts/BIZ-B/secret.jpg")
    except ReceiptImageStoreError as exc:
        assert "does not belong" in str(exc)
    else:
        raise AssertionError("Spaces image retrieval accepted a cross-business key.")


def test_receipt_image_route_serves_private_image_without_cache(tmp_path: Path, monkeypatch):
    import app.ledgergut.web as web_module

    receipt_store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    image_store = LocalReceiptImageStore(receipt_store.image_dir)
    image_key = image_store.put(
        business_id="BIZ-A",
        filename="receipt.jpg",
        data=b"private-image",
        content_type="image/jpeg",
    )
    record_id = receipt_store.save_receipt(
        {"description": "Fasteners", "receipt": {"vendor_name": "Forge Supply"}},
        image_key,
    )

    monkeypatch.setattr(web_module, "_store", receipt_store)
    monkeypatch.setitem(web_module.app.config, "GBO_AUTH_REQUIRED", False)
    monkeypatch.setitem(web_module.app.config, "TESTING", True)
    client = web_module.app.test_client()

    response = client.get(f"/receipts/{record_id}/image")

    assert response.status_code == 200
    assert response.data == b"private-image"
    assert response.mimetype == "image/jpeg"
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_receipt_image_route_does_not_serve_unknown_record(tmp_path: Path, monkeypatch):
    import app.ledgergut.web as web_module

    receipt_store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    monkeypatch.setattr(web_module, "_store", receipt_store)
    monkeypatch.setitem(web_module.app.config, "GBO_AUTH_REQUIRED", False)
    monkeypatch.setitem(web_module.app.config, "TESTING", True)
    client = web_module.app.test_client()

    response = client.get("/receipts/LG-NOTFOUND/image")

    assert response.status_code == 404
