from decimal import Decimal

import pytest

from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Business, Expense
from app.ledgergut.models import BillableStatus, ReceiptExtraction, ReceiptRecord
from app.ledgergut.office_adapter import receipt_record_to_expense


def test_in_memory_store_scopes_records_by_business() -> None:
    store = InMemoryBlackOfficeStore.create()
    store.businesses.save(Business(business_id="biz-a", name="Oasis"))
    store.businesses.save(Business(business_id="biz-b", name="Other"))
    store.expenses.save(
        Expense(
            expense_id="exp-a",
            business_id="biz-a",
            project_id=None,
            amount=Decimal("10.00"),
            currency="CAD",
            description="Fasteners",
        )
    )
    store.expenses.save(
        Expense(
            expense_id="exp-b",
            business_id="biz-b",
            project_id=None,
            amount=Decimal("20.00"),
            currency="CAD",
            description="Paint",
        )
    )

    assert [item.expense_id for item in store.expenses.list_for_business("biz-a")] == [
        "exp-a"
    ]


def test_ledgergut_receipt_maps_to_shared_expense() -> None:
    record = ReceiptRecord(
        record_id="LG-ABC12345",
        submitted_by="steve",
        description="Tile for Alexander",
        currency="cad",
        billable_status=BillableStatus.BILLABLE,
        receipt=ReceiptExtraction(
            vendor_name="Supplier",
            receipt_date="2026-09-08",
            total_amount="183.47",
        ),
    )

    expense = receipt_record_to_expense(
        record,
        business_id="biz-oasis",
        project_id="project-alexander",
    )

    assert expense.expense_id == "LG-ABC12345"
    assert expense.business_id == "biz-oasis"
    assert expense.project_id == "project-alexander"
    assert expense.amount == Decimal("183.47")
    assert expense.currency == "CAD"
    assert expense.billable is True
    assert expense.source_goblin == "ledgergut"
    assert expense.source_record_id == "LG-ABC12345"


def test_ledgergut_adapter_requires_confirmed_total_and_record_id() -> None:
    without_total = ReceiptRecord(
        record_id="LG-NOTOTAL",
        submitted_by="steve",
        description="Unknown receipt",
        currency="CAD",
        receipt=ReceiptExtraction(),
    )
    with pytest.raises(ValueError, match="total_amount"):
        receipt_record_to_expense(without_total, business_id="biz-oasis")

    without_id = ReceiptRecord(
        submitted_by="steve",
        description="Unsaved receipt",
        currency="CAD",
        receipt=ReceiptExtraction(total_amount="10.00"),
    )
    with pytest.raises(ValueError, match="record_id"):
        receipt_record_to_expense(without_id, business_id="biz-oasis")
