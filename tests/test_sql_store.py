from decimal import Decimal

from app.core.models import Agreement, AgreementStatus, Business, Expense
from app.core.sql_store import SqlBlackOfficeStore


def test_sql_store_survives_new_store_instance(tmp_path):
    url = f"sqlite:///{tmp_path / 'office.db'}"
    first = SqlBlackOfficeStore(url)
    first.businesses.save(Business(business_id="BIZ-1", name="Forge Ltd"))
    first.agreements.save(
        Agreement(
            agreement_id="AGR-1",
            business_id="BIZ-1",
            project_id="PRJ-1",
            title="Build it",
            scope="Defined work",
            amount=Decimal("1234.56"),
            currency="CAD",
            status=AgreementStatus.DRAFT,
        )
    )

    second = SqlBlackOfficeStore(url)
    agreement = second.agreements.get("BIZ-1", "AGR-1")
    assert agreement is not None
    assert agreement.amount == Decimal("1234.56")
    assert agreement.status == AgreementStatus.DRAFT


def test_sql_store_enforces_tenant_scope(tmp_path):
    store = SqlBlackOfficeStore(f"sqlite:///{tmp_path / 'tenant.db'}")
    store.expenses.save(
        Expense(
            expense_id="EXP-1",
            business_id="BIZ-A",
            project_id="PRJ-1",
            amount=Decimal("42.10"),
            currency="CAD",
            description="Fasteners",
        )
    )
    assert store.expenses.get("BIZ-A", "EXP-1") is not None
    assert store.expenses.get("BIZ-B", "EXP-1") is None
    assert store.expenses.list_for_business("BIZ-B") == []


def test_sql_store_preserves_decimal_money(tmp_path):
    store = SqlBlackOfficeStore(f"sqlite:///{tmp_path / 'money.db'}")
    expense = Expense(
        expense_id="EXP-MONEY",
        business_id="BIZ-1",
        project_id=None,
        amount=Decimal("0.10"),
        currency="CAD",
        description="Tiny but exact",
    )
    store.expenses.save(expense)
    loaded = store.expenses.get("BIZ-1", "EXP-MONEY")
    assert loaded is not None
    assert loaded.amount == Decimal("0.10")
    assert isinstance(loaded.amount, Decimal)
