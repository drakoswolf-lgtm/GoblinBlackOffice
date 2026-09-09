from pathlib import Path

from app.ledgergut.image_store import LocalReceiptImageStore
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
