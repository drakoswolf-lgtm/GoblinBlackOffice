"""Æterna command intelligence: truthfulness, tenancy and non-mutating navigation."""

from dataclasses import replace
from decimal import Decimal

from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import (
    Agreement, AgreementStatus, Business, Expense, Invoice, InvoiceStatus,
    MaterialPlan, Payment, Project, RecordStatus, ShoppingListItem, WorkLog,
)
from app.office.command import build_command_briefing, resolve_view
from app.office.web import office_app


def store_with_businesses():
    store = InMemoryBlackOfficeStore.create()
    store.businesses.save(Business(business_id="BIZ-A", name="Tenant A", reporting_currency="CAD"))
    store.businesses.save(Business(business_id="BIZ-B", name="Tenant B", reporting_currency="USD"))
    store.projects.save(Project(project_id="JOB-A", business_id="BIZ-A", client_id=None, name="Cedar job"))
    store.projects.save(Project(project_id="JOB-B", business_id="BIZ-B", client_id=None, name="Private rival job"))
    return store


def test_briefing_infers_next_actions_without_claiming_compliance_or_receipts():
    store = store_with_businesses()
    brief = build_command_briefing(store, "BIZ-A", project_id="JOB-A")
    assert brief.project.name == "Cedar job"
    assert brief.currency == "CAD"
    assert brief.active_count == 1
    assert brief.ledger.invoiced == Decimal("0")
    assert brief.actions[0].title == "Define the job agreement"
    assert brief.actions[0].href == "/signor/?project_id=JOB-A"
    checks = {item.name: item for item in brief.project_brief.checks}
    assert checks["Ledgergut"].state == "NO PROJECT EXPENSES"
    assert "does not prove" in checks["Ledgergut"].summary
    assert checks["Grimscratch"].state == "NOT AUTOMATED"
    assert "No clearance" in checks["Grimscratch"].summary


def test_financial_summary_excludes_drafts_foreign_currencies_and_tenants():
    store = store_with_businesses()
    store.invoices.save(Invoice(
        invoice_id="INV-A", business_id="BIZ-A", project_id="JOB-A", client_id="CLIENT-A",
        total=Decimal("500"), status=InvoiceStatus.APPROVED, currency="CAD",
    ))
    store.invoices.save(Invoice(
        invoice_id="INV-DRAFT", business_id="BIZ-A", project_id="JOB-A", client_id="CLIENT-A",
        total=Decimal("10000"), status=InvoiceStatus.DRAFT, currency="CAD",
    ))
    store.invoices.save(Invoice(
        invoice_id="INV-OTHER", business_id="BIZ-A", project_id="JOB-A", client_id="CLIENT-A",
        total=Decimal("2000"), status=InvoiceStatus.APPROVED, currency="USD",
    ))
    store.invoices.save(Invoice(
        invoice_id="INV-B", business_id="BIZ-B", project_id="JOB-B", client_id="CLIENT-B",
        total=Decimal("99999"), status=InvoiceStatus.APPROVED, currency="USD",
    ))
    store.payments.save(Payment(
        payment_id="PAY-A", business_id="BIZ-A", invoice_id="INV-A",
        amount=Decimal("175"), currency="CAD",
    ))
    store.expenses.save(Expense(
        expense_id="EXP-A", business_id="BIZ-A", project_id="JOB-A",
        amount=Decimal("42.50"), currency="CAD", description="Supplies",
    ))
    store.expenses.save(Expense(
        expense_id="EXP-B", business_id="BIZ-B", project_id="JOB-B",
        amount=Decimal("1000"), currency="USD", description="Foreign expense",
    ))
    store.work_logs.save(WorkLog(
        work_log_id="WL-A", business_id="BIZ-A", project_id="JOB-A",
        description="Framing", hours=Decimal("7.5"),
    ))
    report = build_command_briefing(store, "BIZ-A", project_id="JOB-A", question="What is outstanding?")
    assert report.view == "totals"
    assert report.actual_hours == Decimal("7.5")
    assert report.ledger.invoiced == Decimal("500")
    assert report.ledger.paid == Decimal("175")
    assert report.ledger.outstanding == Decimal("325")
    assert report.ledger.expenses == Decimal("42.50")
    assert report.ledger.net_cash == Decimal("132.50")
    assert any(action.title == "Review draft invoices" for action in report.actions)
    assert any(action.title == "Review outstanding balance" for action in report.actions)
    portfolio = build_command_briefing(store, "BIZ-A")
    assert portfolio.ledger.invoiced == Decimal("500")
    assert len(portfolio.portfolio_checks) == 6
    assert "99999" not in str(portfolio.portfolio_checks)
    assert next(c for c in portfolio.portfolio_checks if c.name == "Squarmish").state == "DRAFTS FOR REVIEW"
    assert "Private rival" not in str(portfolio.projects)


def test_materials_and_completed_jobs_have_distinct_action_prompts():
    store = store_with_businesses()
    job = store.projects.get("JOB-A", "BIZ-A")
    store.projects.save(replace(job, status=RecordStatus.COMPLETED))
    store.shopping_items.save(ShoppingListItem(
        shopping_item_id="ITEM-A", business_id="BIZ-A", project_id="JOB-A",
        material_plan_id="PLAN-A", description="Fasteners",
        quantity_required=Decimal("10"), quantity_acquired=Decimal("2"), unit="ea",
    ))
    store.material_plans.save(MaterialPlan(
        material_plan_id="PLAN-A", business_id="BIZ-A", project_id="JOB-A",
        agreement_id=None, estimate_id=None, title="Supplies", approved=True,
    ))
    store.work_logs.save(WorkLog(
        work_log_id="WL-CLOSE", business_id="BIZ-A", project_id="JOB-A",
        description="Installed", hours=Decimal("4"),
    ))
    result = build_command_briefing(store, "BIZ-A", project_id="JOB-A")
    # A field-complete job isn't automatically treated as an unsigned agreement or unpaid invoice.
    titles = [a.title for a in result.actions]
    assert "Review final billing" in titles
    assert "Define the job agreement" not in titles
    checks = {c.name:c for c in result.project_brief.checks}
    assert checks["Packrat"].state == "MATERIALS REMAIN"
    assert checks["Patch"].state == "FIELD COMPLETE"


def test_foreign_project_is_not_accessible_even_with_known_identifier():
    store = store_with_businesses()
    import pytest
    with pytest.raises(LookupError):
        build_command_briefing(store, "BIZ-A", project_id="JOB-B")
    assert build_command_briefing(store, "BIZ-B", project_id="JOB-B").project.name == "Private rival job"


def test_command_router_is_intentionally_narrow():
    assert resolve_view("overview", "Which goblins need checking?")[0] == "checks"
    assert resolve_view("overview", "What is my balance?")[0] == "totals"
    assert resolve_view("overview", "What should I do next?")[0] == "priorities"
    assert resolve_view("checks", "") == ("checks", "")
    assert resolve_view("undefined", "") == ("overview", "")
    assert resolve_view("overview", "Tell me a fairy tale")[1].startswith("LIMITED COMMANDS")


def test_command_route_guards_other_tenant_and_does_not_mutate_records(monkeypatch):
    from app.core.runtime import business_id, office_store
    from app.office import web
    # Use the application's active development business for an authenticated
    # equivalent with real project-scoped records; no state mutation is allowed.
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", False)
    project = Project(
        project_id="CMD-LIVE-A", business_id=business_id,
        client_id=None, name="Command live test",
    )
    office_store.projects.save(project)
    client = office_app.test_client()
    response = client.get("/aeterna/command?project_id=CMD-LIVE-A&view=checks")
    assert response.status_code == 200
    assert b"GOBLIN STATUS REPORT" in response.data
    assert b"NOT AUTOMATED" in response.data
    assert b"Command Intelligence" in response.data
    assert client.get("/aeterna/command?project_id=DOES-NOT-EXIST").status_code == 404
    assert client.post("/aeterna/command", data={"action": "approve"}).status_code == 405
    assert office_store.projects.get(project.project_id, business_id) == project


def test_authenticated_user_must_sign_in_before_command_report(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", True)
    browser = office_app.test_client()
    response = browser.get("/aeterna/command?view=totals")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
