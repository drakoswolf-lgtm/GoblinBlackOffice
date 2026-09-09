from decimal import Decimal
from pathlib import Path

from app.core.memory_store import InMemoryBlackOfficeStore
from app.ledgergut.storage import ReceiptStore


def _valid_form() -> dict[str, str]:
    return {
        "vendor_name": "Home Hardware",
        "receipt_date": "2026-09-08",
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


def test_valid_receipt_publishes_shared_expense(tmp_path: Path, monkeypatch) -> None:
    import app.ledgergut.web as web_module

    receipt_store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    office_store = InMemoryBlackOfficeStore.create()

    monkeypatch.setattr(web_module, "_store", receipt_store)
    monkeypatch.setattr(web_module, "_office_store", office_store)
    monkeypatch.setattr(web_module, "_office_business_id", "biz-test")
    web_module.app.config["TESTING"] = True

    response = web_module.app.test_client().post(
        "/receipts/new",
        data=_valid_form(),
        follow_redirects=True,
    )

    assert response.status_code == 200
    saved_receipts = receipt_store.list_receipts()
    assert len(saved_receipts) == 1

    expenses = office_store.expenses.list_for_business("biz-test")
    assert len(expenses) == 1
    expense = expenses[0]
    assert expense.expense_id == saved_receipts[0]["record_id"]
    assert expense.source_record_id == saved_receipts[0]["record_id"]
    assert expense.amount == Decimal("28.00")
    assert expense.currency == "CAD"
    assert expense.billable is True


def test_invalid_receipt_does_not_publish_shared_expense(tmp_path: Path, monkeypatch) -> None:
    import app.ledgergut.web as web_module

    receipt_store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    office_store = InMemoryBlackOfficeStore.create()

    monkeypatch.setattr(web_module, "_store", receipt_store)
    monkeypatch.setattr(web_module, "_office_store", office_store)
    monkeypatch.setattr(web_module, "_office_business_id", "biz-test")
    web_module.app.config["TESTING"] = True

    invalid_form = _valid_form()
    invalid_form["total_amount"] = "0.00"
    response = web_module.app.test_client().post("/receipts/new", data=invalid_form)

    assert response.status_code == 200
    assert receipt_store.list_receipts() == []
    assert office_store.expenses.list_for_business("biz-test") == []
