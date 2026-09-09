from datetime import date
from decimal import Decimal

from app.core.models import Agreement, AgreementStatus, Expense, InvoiceStatus
from app.squarmish.service import draft_invoice


def _agreement() -> Agreement:
    return Agreement(
        agreement_id="AGR-001",
        business_id="BIZ-001",
        project_id="PRJ-001",
        title="Cabinet work",
        scope="Build cabinet.",
        amount=Decimal("1000.00"),
        currency="CAD",
        status=AgreementStatus.ACCEPTED,
    )


def test_squarmish_builds_invoice_from_agreement_and_billable_expense():
    expense = Expense(
        expense_id="EXP-001",
        business_id="BIZ-001",
        project_id="PRJ-001",
        amount=Decimal("125.50"),
        currency="CAD",
        description="Hardware",
        billable=True,
    )
    result = draft_invoice(
        business_id="BIZ-001",
        agreement=_agreement(),
        client_id="CLI-001",
        expenses=(expense,),
        due_date=date(2026, 10, 1),
    )
    assert result.errors == ()
    assert result.invoice is not None
    assert result.invoice.total == Decimal("1125.50")
    assert result.invoice.status == InvoiceStatus.DRAFT
    assert len(result.lines) == 2
    assert any("Tax has not been applied" in note for note in result.review_notes)


def test_squarmish_excludes_unconfirmed_expense():
    expense = Expense(
        expense_id="EXP-MAYBE",
        business_id="BIZ-001",
        project_id="PRJ-001",
        amount=Decimal("50.00"),
        currency="CAD",
        description="Maybe billable",
        billable=None,
    )
    result = draft_invoice(
        business_id="BIZ-001",
        agreement=_agreement(),
        client_id="CLI-001",
        expenses=(expense,),
    )
    assert result.invoice is not None
    assert result.invoice.total == Decimal("1000.00")
    assert any("not confirmed billable" in note for note in result.review_notes)


def test_squarmish_requires_client_and_rejects_cross_project_expense():
    expense = Expense(
        expense_id="EXP-WRONG",
        business_id="BIZ-001",
        project_id="PRJ-OTHER",
        amount=Decimal("50.00"),
        currency="CAD",
        description="Wrong project",
        billable=True,
    )
    result = draft_invoice(
        business_id="BIZ-001",
        agreement=_agreement(),
        client_id="",
        expenses=(expense,),
    )
    assert result.invoice is None
    assert any("Client is required" in error for error in result.errors)
    assert any("another project" in error for error in result.errors)


def test_office_mounts_all_three_launch_specialists():
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    from app.office.web import application

    client = Client(application, Response)
    desk = client.get("/")
    assert desk.status_code == 200
    assert b"/ledgergut/" in desk.data
    assert b"/signor/" in desk.data
    assert b"/squarmish/" in desk.data
    response = client.get("/squarmish/")
    assert response.status_code == 200
    assert b"Draft the invoice" in response.data
