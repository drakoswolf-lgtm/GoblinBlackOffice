"""Pass D production-mode release gate against a real PostgreSQL service.

Invoke in two *separate Python processes* with an isolated CI database:
  python tests/pass_d_release_gate.py seed
  python tests/pass_d_release_gate.py verify
This validates auth, cinematic bytes, PDF and tenant isolation as well as
persistence across interpreter/application restarts. It never targets live data.
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal

from werkzeug.test import Client
from werkzeug.wrappers import Response

assert os.environ.get("GBO_ENV") == "production", "Run only in isolated production-mode CI"
assert os.environ.get("GBO_AUTH_REQUIRED") == "1"
assert os.environ.get("DATABASE_URL", "").startswith(("postgresql://", "postgres://", "postgresql+psycopg://"))

from app.core.runtime import office_store  # noqa: E402
from app.office.auth import user_id_for_email  # noqa: E402
from app.office.web import application  # noqa: E402
from app.core.models import AgreementStatus, InvoiceStatus  # noqa: E402

BASE = "https://beta-pass-d.test"
ORIGIN = {"Origin": BASE}
EMAIL = "release-gate-primary@example.test"
OTHER = "release-gate-other@example.test"
PASS = "release-gate-correct-password-456"
INVITE = os.environ["GBO_INVITE_TOKEN"]


def browser():
    return Client(application, Response, use_cookies=True)


def get(client, path):
    return client.get(path, base_url=BASE)


def post(client, path, data=None, origin=ORIGIN):
    return client.post(path, data=data or {}, base_url=BASE, headers=origin)


def assert_redirect(response, suffix):
    assert response.status_code == 302, (response.status_code, response.data[:220])
    assert response.headers["Location"].endswith(suffix), response.headers["Location"]


def check_media(client):
    # These requests must pass before onboarding; otherwise the film is HTML
    # redirect masquerading as a video source.
    for asset in (
        "introductions/aeterna-first-entry-desktop.mp4",
        "introductions/aeterna-first-entry-mobile.mp4",
        "characters/aeterna-ambient-portrait.mp4",
        "characters/aeterna-ambient-poster.webp",
        "characters/canon-goblin-specialist-sprite.webp",
        "startup/gbo-opening-desktop.mp4",
        "startup/gbo-opening-mobile.mp4",
    ):
        res = get(client, "/canon/" + asset)
        expected = "video/mp4" if asset.endswith(".mp4") else "image/webp"
        assert res.status_code == 200, (asset, res.status_code, res.headers.get("Location"))
        assert res.mimetype == expected, (asset, res.mimetype)
        assert len(res.data) > 128, (asset, len(res.data))
        if expected == "video/mp4":
            assert res.data[4:8] == b"ftyp", asset
        else:
            assert res.data[:4] == b"RIFF" and res.data[8:12] == b"WEBP", asset


def seed():
    c = browser()
    assert_redirect(get(c, "/"), "/login?next=/")
    assert_redirect(get(c, "/aeterna/command"), "/login?next=/aeterna/command")

    blocked = post(c, "/register", {
        "display_name":"Primary release user", "email":EMAIL,
        "password":PASS, "invite_code":"incorrect",
    })
    assert blocked.status_code == 200 and b"valid private-beta invite" in blocked.data

    wrong_origin = post(c, "/register", {
        "display_name":"Bad origin", "email":"cross-site@example.test",
        "password":PASS, "invite_code":INVITE,
    }, origin={"Origin":"https://attacker.test"})
    assert wrong_origin.status_code == 400, wrong_origin.status_code

    registered = post(c, "/register", {
        "display_name":"Primary release user", "email":EMAIL,
        "password":PASS, "invite_code":INVITE,
    })
    assert_redirect(registered, "/welcome")
    assert get(c,"/welcome").status_code == 200
    assert_redirect(get(c,"/onboarding"),"/welcome")
    check_media(c)

    # The cinematic is character entertainment only; it does not set up a business.
    assert_redirect(post(c,"/welcome"),"/onboarding")
    assert_redirect(get(c,"/welcome"),"/onboarding")
    assert_redirect(post(c,"/onboarding",{
        "business_name":"Release Test Contracting",
        "currency":"CAD",
        "business_type":"Property maintenance",
        "payment_terms":"Net 15",
    }),"/")
    assert get(c,"/").status_code == 200

    job = post(c, "/jobs/new", {
        "client_name":"Release Test Client",
        "client_email":"release-client@example.test",
        "project_name":"Release test cedar repair",
        "description":"Replace cedar boards and capture costs.",
        "pricing_model":"hourly",
    })
    assert job.status_code == 302 and "/jobs/PRJ-" in job.headers["Location"]
    job_url = job.headers["Location"]
    assert b"Receipt Log" in get(c,job_url).data
    assert b"Materials" in get(c,job_url).data
    user = office_store.users.get(user_id_for_email(EMAIL))
    assert user is not None and user.onboarding_complete
    bid=user.business_id
    project=office_store.projects.list_for_business(bid)[0]
    assert project.pricing_model == "hourly"
    client=office_store.clients.get(project.client_id,bid)
    assert client is not None and client.email == "release-client@example.test"
    selected = get(c, "/records?client_id="+client.client_id)
    assert selected.status_code == 200 and b"Release Test Client" in selected.data

    agreement_res = post(c,"/signor/",{
        "project_id":project.project_id,
        "title":"Release gate cedar agreement",
        "scope":"Repair boards and log materials.",
        "amount":"200",
        "currency":"CAD",
    })
    assert agreement_res.status_code == 200, (agreement_res.status_code,agreement_res.data[:250])
    agreement = office_store.agreements.list_for_business(bid)[0]
    approved_agreement=post(c,f"/signor/agreements/{agreement.agreement_id}/confirm")
    assert approved_agreement.status_code == 302
    assert approved_agreement.headers["Location"].startswith(job_url+"?message=")
    assert office_store.agreements.get(agreement.agreement_id,bid).status == AgreementStatus.PROPOSED
    assert get(c, f"/signor/agreements/{agreement.agreement_id}/pdf").mimetype == "application/pdf"

    planned=post(c,job_url,{
        "action":"plan","agreement_id":agreement.agreement_id,
        "labour_hours":"2","labour_rate":"40",
        "material_description":"Cedar board","material_quantity":"2",
        "material_unit":"ea","material_price":"12",
        "approve_materials":"1","other_cost":"0",
    })
    assert planned.status_code == 302, (planned.status_code,planned.data[:200])
    assert len(office_store.shopping_items.list_for_business(bid)) == 1

    work=post(c,job_url,{"action":"work","description":"Repaired cedar fence",
                         "hours":"2","billable":"1"})
    assert work.status_code == 302
    assert len(office_store.work_logs.list_for_business(bid)) == 1

    receipt=post(c,"/ledgergut/receipts/new",{
        "vendor_name":"Release Supply","receipt_date":"2026-10-11",
        "description":"Cedar boards","office_project_id":project.project_id,
        "project_name":project.name,"expense_category":"materials",
        "subtotal":"24.00","tax_amount":"0.00","total_amount":"24.00",
        "currency":"CAD","line_items_text":"Cedar board | 2 | 12",
        "paid_by":"operator","reimbursement_status":"not_reimbursed",
        "billable_status":"billable","submitted_by":"Release gate",
    })
    assert receipt.status_code == 302, (receipt.status_code, receipt.data[:220])
    assert len(office_store.expenses.list_for_business(bid)) == 1
    assert office_store.shopping_items.list_for_business(bid)[0].quantity_remaining == Decimal("0")

    invoiced=post(c,job_url,{"action":"invoice","agreement_id":agreement.agreement_id,
                            "labour_rate":"40","include_agreement_amount":"1"})
    assert invoiced.status_code == 302
    invoice=office_store.invoices.list_for_business(bid)[0]
    assert invoice.total > Decimal("0")
    assert get(c,f"/squarmish/invoices/{invoice.invoice_id}/pdf").mimetype == "application/pdf"
    assert post(c,f"/squarmish/invoices/{invoice.invoice_id}/confirm").status_code == 302
    assert office_store.invoices.get(invoice.invoice_id,bid).status == InvoiceStatus.APPROVED
    assert post(c,job_url,{"action":"payment","invoice_id":invoice.invoice_id,
                          "amount":"20"}).status_code == 302
    assert office_store.invoices.get(invoice.invoice_id,bid).status == InvoiceStatus.PARTIALLY_PAID
    report=get(c,f"/aeterna/command?project_id={project.project_id}&view=totals")
    assert report.status_code == 200 and b"PROJECT TOTALS" in report.data
    assert b"NOT AUTOMATED" in get(c,f"/aeterna/command?project_id={project.project_id}&view=checks").data
    assert post(c,"/logout").status_code == 302
    assert_redirect(get(c,job_url),"/login?next="+job_url)
    print("PASS production-mode seed: invite, cinematic, CV, client, scope, PDF, materials, receipt, labour, invoice, payment, command")


def verify():
    # A NEW process imports/opens the persisted PostgreSQL store. This is a
    # process restart, not an in-memory test or a redeployment of the live app.
    c=browser()
    user=office_store.users.get(user_id_for_email(EMAIL))
    assert user is not None and user.onboarding_complete
    bid=user.business_id
    projects=office_store.projects.list_for_business(bid)
    assert len(projects) == 1
    project=projects[0]
    invoice=office_store.invoices.list_for_business(bid)[0]
    agreement=office_store.agreements.list_for_business(bid)[0]
    assert len(office_store.expenses.list_for_business(bid)) == 1
    assert len(office_store.payments.list_for_business(bid)) == 1
    assert invoice.status == InvoiceStatus.PARTIALLY_PAID
    assert office_store.shopping_items.list_for_business(bid)[0].quantity_remaining == 0

    login=post(c,"/login",{"email":EMAIL,"password":PASS})
    assert_redirect(login,"/")
    assert get(c,"/welcome").status_code == 302
    assert get(c,f"/jobs/{project.project_id}").status_code == 200
    assert get(c,f"/signor/agreements/{agreement.agreement_id}/pdf").mimetype == "application/pdf"
    assert get(c,f"/squarmish/invoices/{invoice.invoice_id}/pdf").mimetype == "application/pdf"
    assert post(c,"/logout").status_code == 302

    other=post(c,"/register",{
        "display_name":"Other beta operator","email":OTHER,
        "password":PASS,"invite_code":INVITE,
    })
    assert_redirect(other,"/welcome")
    assert_redirect(post(c,"/welcome"),"/onboarding")
    assert_redirect(post(c,"/onboarding",{
        "business_name":"Another Black Office","currency":"USD",
    }),"/")
    assert get(c,f"/jobs/{project.project_id}").status_code == 404
    assert get(c,f"/aeterna/command?project_id={project.project_id}").status_code == 404
    assert get(c,f"/signor/agreements/{agreement.agreement_id}/pdf").status_code == 404
    assert get(c,f"/squarmish/invoices/{invoice.invoice_id}/pdf").status_code == 404
    assert b"Release Test Client" not in get(c,"/records").data
    print("PASS PostgreSQL persistence across process restart; returning login, tenant records, PDF and command isolation")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "seed": seed()
    elif mode == "verify": verify()
    else: raise SystemExit("Usage: pass_d_release_gate.py seed|verify")
