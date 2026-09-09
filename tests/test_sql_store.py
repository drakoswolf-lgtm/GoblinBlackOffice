from decimal import Decimal

from app.core.models import Agreement, AgreementStatus, Business, Expense, Invoice, InvoiceLineItem
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
    agreement = second.agreements.get("AGR-1", "BIZ-1")
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
    assert store.expenses.get("EXP-1", "BIZ-A") is not None
    assert store.expenses.get("EXP-1", "BIZ-B") is None
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
    loaded = store.expenses.get("EXP-MONEY", "BIZ-1")
    assert loaded is not None
    assert loaded.amount == Decimal("0.10")
    assert isinstance(loaded.amount, Decimal)


def test_sql_store_round_trips_invoice_line_items(tmp_path):
    url = f"sqlite:///{tmp_path / 'invoice.db'}"
    first = SqlBlackOfficeStore(url)
    first.invoices.save(
        Invoice(
            invoice_id="SQ-1",
            business_id="BIZ-1",
            project_id="PRJ-1",
            client_id="CLI-1",
            total=Decimal("128.50"),
            subtotal=Decimal("128.50"),
            agreement_id="AGR-1",
            line_items=(
                InvoiceLineItem(description="Labour", amount=Decimal("100.00"), source_type="agreement", source_id="AGR-1"),
                InvoiceLineItem(description="Fasteners", amount=Decimal("28.50"), source_type="expense", source_id="EXP-1"),
            ),
            review_notes=("Tax unresolved.",),
        )
    )

    second = SqlBlackOfficeStore(url)
    invoice = second.invoices.get("SQ-1", "BIZ-1")
    assert invoice is not None
    assert invoice.agreement_id == "AGR-1"
    assert invoice.subtotal == Decimal("128.50")
    assert invoice.line_items[0].description == "Labour"
    assert invoice.line_items[1].amount == Decimal("28.50")
    assert invoice.review_notes == ("Tax unresolved.",)
