"""Pass A regression checks for field usability and safe project closeout."""
from decimal import Decimal

from werkzeug.datastructures import MultiDict
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.core.job_lifecycle import draft_job_plan
from app.core.models import Agreement, AgreementStatus, RecordStatus
from app.core.runtime import business_id, office_store
from app.ledgergut.form_mapper import build_models
from app.office.records import create_client, create_project
from app.office.web import application
from app.packrat.service import MaterialRequirementInput


def _open_project(label="Beta A"):
    client, errors = create_client(business_id=business_id, name=label + " client")
    assert not errors
    project, errors = create_project(
        business_id=business_id, client_id=client.client_id,
        name=label + " project", pricing_model="hourly",
    )
    assert not errors
    return project


def test_hourly_project_can_exist_without_agreed_fixed_price():
    project = _open_project("Hourly intake")
    assert project.pricing_model == "hourly"
    assert project.status == RecordStatus.ACTIVE
    agreement = Agreement(
        agreement_id="AGR-A-HOURLY", business_id=business_id,
        project_id=project.project_id, title="Hourly", scope="Hours as worked.",
        amount=None, status=AgreementStatus.ACCEPTED,
    )
    draft = draft_job_plan(
        business_id=business_id, agreement=agreement,
        labour_hours="", labour_rate="40", materials=(),
    )
    assert draft.errors == ()
    assert draft.estimate.labour_rate == Decimal("40")
    assert draft.estimate.labour_hours_estimate is None


def test_material_rows_are_parsed_as_independent_fields():
    project = _open_project("Structured materials")
    agreement = Agreement(
        agreement_id="AGR-A-ROWS", business_id=business_id,
        project_id=project.project_id, title="Cedar", scope="Build fence.",
        status=AgreementStatus.ACCEPTED,
    )
    office_store.agreements.save(agreement)
    client = Client(application, Response)
    response = client.post(
        f"/jobs/{project.project_id}",
        data=MultiDict([
            ("action", "plan"), ("agreement_id", agreement.agreement_id),
            ("labour_hours", ""), ("labour_rate", "40"),
            ("material_description", "Cedar board"),
            ("material_quantity", "12"),
            ("material_unit", "ea"),
            ("material_price", "7.49"),
            ("material_description", "Post anchor"),
            ("material_quantity", "2"),
            ("material_unit", "ea"),
            ("material_price", "19.50"),
            ("other_cost", "0"), ("approve_materials", "1")
        ]),
    )
    assert response.status_code == 302
    rows = [x for x in office_store.shopping_items.list_for_business(business_id) if x.project_id == project.project_id]
    assert len(rows) == 2
    assert rows[0].description == "Cedar board"
    assert rows[0].quantity_required == Decimal("12")
    assert rows[1].estimated_unit_cost == Decimal("19.50")


def test_ledgergut_structured_line_items_and_manual_entry_panel():
    record, errors = build_models({
        "description": "Fasteners",
        "total_amount": "24.00",
        "_structured_line_rows": [("Screws", "3", "8.00"), ("", "", "")],
    })
    assert errors == []
    assert record.receipt.line_items[0].name == "Screws"
    assert record.receipt.line_items[0].unit_price == Decimal("8.00")
    client = Client(application, Response)
    page = client.get("/ledgergut/")
    assert page.status_code == 200
    assert b"Scan with Camera" in page.data
    assert b"Enter Manually" in page.data
    assert b'data-receipt-review' in page.data


def test_project_completion_archive_and_reopen_retains_record():
    project = _open_project("Closeout")
    client = Client(application, Response)
    result = client.post(
        f"/jobs/{project.project_id}",
        data={"action": "project_status", "status": "completed"},
    )
    assert result.status_code == 302
    assert office_store.projects.get(project.project_id, business_id).status == RecordStatus.COMPLETED
    result = client.post(
        f"/jobs/{project.project_id}",
        data={"action": "project_status", "status": "archived"},
    )
    assert result.status_code == 302
    assert office_store.projects.get(project.project_id, business_id).status == RecordStatus.ARCHIVED
    assert project.name.encode() in client.get("/records").data
    assert project.name.encode() not in client.get("/").data
    result = client.post(
        f"/jobs/{project.project_id}",
        data={"action": "project_status", "status": "active"},
    )
    assert result.status_code == 302
    assert office_store.projects.get(project.project_id, business_id).status == RecordStatus.ACTIVE


def test_rejects_unknown_pricing_basis():
    project = _open_project("Price options")
    _, errors = create_project(
        business_id=business_id, client_id=project.client_id,
        name="Invalid model", pricing_model="surprise!",
    )
    assert errors
