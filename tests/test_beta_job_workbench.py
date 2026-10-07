from datetime import date
from decimal import Decimal

from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.core.job_lifecycle import draft_job_plan, persist_job_plan
from app.core.models import Agreement, AgreementStatus, Invoice, InvoiceStatus
from app.core.runtime import business_id, office_store
from app.ledgergut.form_mapper import build_models
from app.office.records import create_client, create_project
from app.office.web import application
from app.packrat.service import MaterialRequirementInput


def _project(prefix: str):
    client, errors = create_client(
        business_id=business_id,
        name=f"{prefix} Client",
    )
    assert errors == ()
    project, errors = create_project(
        business_id=business_id,
        client_id=client.client_id,
        name=f"{prefix} Project",
        description="Beta lifecycle test",
    )
    assert errors == ()
    return project


def test_office_desk_exposes_connected_new_job_flow():
    client = Client(application, Response)

    desk = client.get("/")
    assert desk.status_code == 200
    assert b'href="/jobs/new"' in desk.data

    intake = client.get("/jobs/new")
    assert intake.status_code == 200
    assert b"Open a new job" in intake.data


def test_job_workbench_is_clickable_for_existing_project():
    project = _project("Workbench")
    client = Client(application, Response)

    response = client.get(f"/jobs/{project.project_id}")

    assert response.status_code == 200
    assert b"Job Workbench" in response.data
    assert b"Estimate + material plan" not in response.data
    assert b"Draft agreement" in response.data


def test_receipt_form_mapper_preserves_verified_purchase_lines():
    record, errors = build_models(
        {
            "description": "Fence materials",
            "currency": "CAD",
            "line_items_text": "1x6 cedar fence board | 6 | 7.49\n4x4 cedar post | 2 | 34.95",
        }
    )

    assert errors == []
    assert record is not None
    assert len(record.receipt.line_items) == 2
    assert record.receipt.line_items[0].quantity == Decimal("6")
    assert record.receipt.line_items[1].unit_price == Decimal("34.95")


def test_saving_project_receipt_updates_packrat_shopping_quantities():
    project = _project("ReceiptReconcile")
    agreement = Agreement(
        agreement_id="AGR-BETA-RECEIPT",
        business_id=business_id,
        project_id=project.project_id,
        title="Cedar fence",
        scope="Build cedar fence.",
        amount=None,
        currency="CAD",
        status=AgreementStatus.ACCEPTED,
    )
    office_store.agreements.save(agreement)
    draft = draft_job_plan(
        business_id=business_id,
        agreement=agreement,
        labour_hours="8",
        labour_rate="40",
        materials=(
            MaterialRequirementInput(
                description="1x6 cedar fence board",
                quantity="10",
                unit="ea",
                estimated_unit_cost="7.49",
            ),
        ),
    )
    assert draft.errors == ()
    persist_job_plan(office_store, draft, approve_materials=True)

    client = Client(application, Response)
    response = client.post(
        "/ledgergut/receipts/new",
        data={
            "vendor_name": "Beta Building Supply",
            "receipt_date": date.today().isoformat(),
            "description": "Fence boards",
            "office_project_id": project.project_id,
            "project_name": project.name,
            "expense_category": "materials",
            "subtotal": "14.98",
            "tax_amount": "0.00",
            "total_amount": "14.98",
            "currency": "CAD",
            "line_items_text": "1x6 cedar fence board | 2 | 7.49",
            "paid_by": "steve",
            "reimbursement_status": "not_reimbursed",
            "billable_status": "billable",
            "submitted_by": "beta tester",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/jobs/{project.project_id}?message=receipt-saved"
    )
    items = [
        item
        for item in office_store.shopping_items.list_for_business(business_id)
        if item.project_id == project.project_id
    ]
    assert len(items) == 1
    assert items[0].quantity_acquired == Decimal("2")
    assert items[0].quantity_remaining == Decimal("8")
    assert items[0].actual_cost == Decimal("14.98")


def test_specialist_approvals_return_to_project_workbench():
    project = _project("Handoff")
    agreement = Agreement(
        agreement_id="AGR-HANDOFF",
        business_id=business_id,
        project_id=project.project_id,
        title="Handoff agreement",
        scope="Defined scope.",
        amount=Decimal("100.00"),
        currency="CAD",
        status=AgreementStatus.DRAFT,
    )
    office_store.agreements.save(agreement)

    client = Client(application, Response)
    response = client.post(f"/signor/agreements/{agreement.agreement_id}/confirm")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/jobs/{project.project_id}?message=agreement-ready"
    )

    invoice = Invoice(
        invoice_id="SQ-HANDOFF",
        business_id=business_id,
        project_id=project.project_id,
        client_id=project.client_id or "",
        total=Decimal("100.00"),
        currency="CAD",
        status=InvoiceStatus.DRAFT,
        agreement_id=agreement.agreement_id,
    )
    office_store.invoices.save(invoice)
    response = client.post(f"/squarmish/invoices/{invoice.invoice_id}/confirm")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/jobs/{project.project_id}?message=invoice-approved"
    )


def test_existing_project_can_be_resumed_from_office_desk_and_records():
    project = _project("Resume")
    client = Client(application, Response)

    desk = client.get("/")
    assert desk.status_code == 200
    assert project.name.encode() in desk.data
    assert f'href="/jobs/{project.project_id}"'.encode() in desk.data

    records = client.get("/records")
    assert records.status_code == 200
    assert f'href="/jobs/{project.project_id}"'.encode() in records.data
