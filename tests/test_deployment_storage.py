from pathlib import Path

from app.ledgergut.image_store import LocalReceiptImageStore, build_receipt_image_store
from app.ledgergut.sql_storage import SqlReceiptStore


def test_sql_receipt_store_survives_new_instance_and_scopes_business(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'receipts.db'}"
    active = {"business_id": "BIZ-A"}
    provider = lambda: active["business_id"]

    first = SqlReceiptStore(url, provider)
    record_id = first.save_receipt({"description": "Fasteners", "receipt": {"vendor_name": "Store"}}, "receipts/BIZ-A/x.jpg")

    second = SqlReceiptStore(url, provider)
    rows = second.list_receipts()
    assert len(rows) == 1
    assert rows[0]["record_id"] == record_id
    assert rows[0]["image_filename"] == "receipts/BIZ-A/x.jpg"

    active["business_id"] = "BIZ-B"
    assert second.list_receipts() == []


def test_local_receipt_image_store_round_trip(tmp_path: Path):
    store = LocalReceiptImageStore(tmp_path)
    key = store.put(business_id="BIZ-A", filename="receipt.jpg", data=b"abc", content_type="image/jpeg")
    assert key == "receipt.jpg"
    assert (tmp_path / key).read_bytes() == b"abc"
    store.delete(key)
    assert not (tmp_path / key).exists()


def test_endpoint_metadata_without_spaces_credentials_uses_local_storage(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SPACES_ENDPOINT_URL", "https://tor1.digitaloceanspaces.com")
    monkeypatch.setenv("SPACES_REGION", "tor1")
    monkeypatch.delenv("SPACES_BUCKET", raising=False)
    monkeypatch.delenv("SPACES_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("SPACES_SECRET_ACCESS_KEY", raising=False)

    store = build_receipt_image_store(tmp_path)

    assert isinstance(store, LocalReceiptImageStore)


def test_partial_spaces_credentials_still_fail_loudly(tmp_path: Path, monkeypatch):
    import pytest

    monkeypatch.setenv("SPACES_ENDPOINT_URL", "https://tor1.digitaloceanspaces.com")
    monkeypatch.setenv("SPACES_BUCKET", "receipts")
    monkeypatch.delenv("SPACES_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("SPACES_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Spaces configuration is incomplete"):
        build_receipt_image_store(tmp_path)
