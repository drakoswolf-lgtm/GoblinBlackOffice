"""Beta heart checks: fail-closed configuration and a real authenticated job."""
from decimal import Decimal

import pytest
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.core.deployment import validate_deployment_settings
from app.core.models import AgreementStatus, InvoiceStatus
from app.core.runtime import office_store
from app.ledgergut.web import app as ledgergut_app
from app.office.auth import user_id_for_email
from app.office.web import application, office_app
from app.signor.web import app as signor_app
from app.squarmish.web import app as squarmish_app


def _production(**changes):
    settings = {
        "GBO_ENV": "production",
        "GBO_AUTH_REQUIRED": "1",
        "GBO_SECRET": "example-long-secret",
        "GBO_INVITE_TOKEN": "sample-invite",
        "DATABASE_URL": "postgresql+psycopg://user:pass@db.example/gbo",
        "WEB_CONCURRENCY": "2",
    }
    settings.update(changes)
    return settings


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"GBO_AUTH_REQUIRED": "0"}, "GBO_AUTH_REQUIRED"),
        ({"GBO_AUTH_REQUIRED": ""}, "GBO_AUTH_REQUIRED"),
        ({"GBO_SECRET": ""}, "GBO_SECRET"),
        ({"GBO_INVITE_TOKEN": ""}, "GBO_INVITE_TOKEN"),
        ({"DATABASE_URL": ""}, "DATABASE_URL"),
        ({"DATABASE_URL": "sqlite:////tmp/gbo.db"}, "PostgreSQL"),
    ],
)
def test_production_fails_closed(change, error):
    with pytest.raises(RuntimeError, match=error):
        validate_deployment_settings(_production(**change))


def test_internal_memory_smoke_is_explicit_and_single_worker():
    with pytest.raises(RuntimeError, match="multiple workers"):
        validate_deployment_settings(
            _production(DATABASE_URL="", GBO_INTERNAL_SMOKE_TEST="1", WEB_CONCURRENCY="2")
        )
    validate_deployment_settings(
        _production(DATABASE_URL="", GBO_INTERNAL_SMOKE_TEST="1", WEB_CONCURRENCY="1")
    )


def test_real_database_supports_multiple_workers_and_local_memory_does_not():
    validate_deployment_settings(_production())
    validate_deployment_settings({"GBO_ENV": "development", "WEB_CONCURRENCY": "1"})
    with pytest.raises(RuntimeError, match="multiple workers"):
        validate_deployment_settings({"GBO_ENV": "development", "WEB_CONCURRENCY": "3"})


def test_authenticated_client_to_invoice_to_payment_browser_contract(monkeypatch):
    # Exercise the actual DispatcherMiddleware routes with the same login cookie.
    for app in (office_app, ledgergut_app, signor_app, squarmish_app):
        monkeypatch.setitem(app.config, "GBO_AUTH_REQUIRED", True)
    monkeypatch.setitem(office_app.config, "GBO_INVITE_TOKEN", "test-private-beta")
    monkeypatch.setitem(office_app.config, "GBO_SAME_ORIGIN_PROTECTION", False)

    browser = Client(application, Response, use_cookies=True)
    for path in ("/", "/records", "/jobs/new", "/signor/", "/squarmish/", "/ledgergut/"):
        locked = browser.get(path)
        assert locked.status_code == 302, path
        assert "/login" in locked.headers["Location"], path

    registration = {
        "display_name": "Heart Test Commander",
        "email": "heart-beta@example.test",
        "password": "heart-test-password-456",
    }
    denied = browser.post("/register", data={**registration, "invite_code": "bad"})
    assert denied.status_code == 200
    assert b"valid private-beta invite code" in denied.data

    created = browser.post(
        "/register", data={**registration, "invite_code": "test-private-beta"}
    )
    assert created.status_code == 302
    assert created.headers["Location"].endswith("/onboarding")
    assert browser.get("/jobs/new").headers["Location"].endswith("/onboarding")
    assert browser.get("/signor/").headers["Location"].endswith("/onboarding")

    intro = browser.get("/onboarding")
    assert intro.status_code == 200
    done = browser.post(
        "/onboarding",
        data={"business_name": "Heart Test Contracting", "currency": "CAD"},
    )
    assert done.status_code == 302
    assert done.headers["Location"].endswith("/")

    user = office_store.users.get(user_id_for_email(registration["email"]))
    assert user is not None and user.onboarding_complete
    business_id = user.business_id

    created_job = browser.post(
        "/jobs/new",
        data={
            "client_name": "Heart Test Client",
            "client_email": "client@example.test",
            "project_name": "Repair a cedar gate",
            "description": "Rehang gate and replace hinge screws.",
        },
    )
    assert created_job.status_code == 302
    job_url = created_job.headers["Location"]
    assert "/jobs/PRJ-" in job_url
    assert b"Repair a cedar gate" in browser.get(job_url).data

    project = office_store.projects.list_for_business(business_id)[0]
    assert office_store.clients.get(project.client_id, business_id).name == "Heart Test Client"
    agreement_result = browser.post(
        "/signor/",
        data={
            "project_id": project.project_id,
            "title": "Gate repair agreement",
            "scope": "Rehang cedar gate and replace hinge screws",
            "amount": "200",
            "currency": "CAD",
        },
    )
    assert agreement_result.status_code == 200
    agreement = office_store.agreements.list_for_business(business_id)[0]
    assert agreement.status == AgreementStatus.DRAFT
    approved = browser.post(f"/signor/agreements/{agreement.agreement_id}/confirm")
    assert approved.status_code == 302
    assert office_store.agreements.get(agreement.agreement_id, business_id).status == AgreementStatus.PROPOSED
    assert browser.get(f"/signor/agreements/{agreement.agreement_id}/pdf").mimetype == "application/pdf"

    planned = browser.post(
        job_url,
        data={
            "action": "plan",
            "agreement_id": agreement.agreement_id,
            "labour_hours": "2",
            "labour_rate": "40",
            "materials_text": "Hinge screws | 1 | box | 12",
            "approve_materials": "1",
        },
    )
    assert planned.status_code == 302
    assert len(office_store.estimates.list_for_business(business_id)) == 1
    assert len(office_store.shopping_items.list_for_business(business_id)) == 1

    work = browser.post(
        job_url,
        data={"action": "work", "description": "Gate rehung", "hours": "2", "billable": "1"},
    )
    assert work.status_code == 302
    assert len(office_store.work_logs.list_for_business(business_id)) == 1

    draft = browser.post(
        job_url,
        data={
            "action": "invoice",
            "agreement_id": agreement.agreement_id,
            "labour_rate": "40",
            "include_agreement_amount": "1",
        },
    )
    assert draft.status_code == 302
    invoice = office_store.invoices.list_for_business(business_id)[0]
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.total > Decimal("0")
    assert browser.get(f"/squarmish/invoices/{invoice.invoice_id}/pdf").mimetype == "application/pdf"

    invoice_approved = browser.post(f"/squarmish/invoices/{invoice.invoice_id}/confirm")
    assert invoice_approved.status_code == 302
    assert office_store.invoices.get(invoice.invoice_id, business_id).status == InvoiceStatus.APPROVED
    payment = browser.post(
        job_url, data={"action": "payment", "invoice_id": invoice.invoice_id, "amount": "20"}
    )
    assert payment.status_code == 302
    assert office_store.invoices.get(invoice.invoice_id, business_id).status == InvoiceStatus.PARTIALLY_PAID
    assert b"Payment recorded" in browser.get(payment.headers["Location"]).data

    # A different business cannot retrieve this client's project or commercial PDFs.
    assert browser.post("/logout").status_code == 302
    assert browser.get(job_url).status_code == 302
    other = browser.post(
        "/register",
        data={
            "display_name": "Other Commander",
            "email": "heart-beta-other@example.test",
            "password": "other-test-password-456",
            "invite_code": "test-private-beta",
        },
    )
    assert other.status_code == 302
    assert browser.post(
        "/onboarding", data={"business_name": "Other Black Office", "currency": "CAD"}
    ).status_code == 302
    assert browser.get(job_url).status_code == 404
    assert browser.get(f"/signor/agreements/{agreement.agreement_id}/pdf").status_code == 404
    assert browser.get(f"/squarmish/invoices/{invoice.invoice_id}/pdf").status_code == 404
