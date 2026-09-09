from decimal import Decimal

from app.core.models import AgreementStatus
from app.signor.service import AgreementDraftInput, draft_agreement


def test_signor_drafts_explicit_agreement():
    result = draft_agreement(
        AgreementDraftInput(
            project_id="PRJ-001",
            title="Reception desk finishing",
            scope="Finish tile and trim on reception desk.",
            amount="1250",
            assumptions="Existing substrate is sound.",
            exclusions="Electrical work.",
            payment_terms="Due on completion.",
            change_order_terms="Additional work requires written approval.",
        ),
        business_id="BIZ-001",
    )
    assert result.errors == ()
    assert result.agreement is not None
    assert result.agreement.amount == Decimal("1250.00")
    assert result.agreement.status == AgreementStatus.DRAFT
    assert "Assumptions:" in result.agreement.scope
    assert "Electrical work." in result.agreement.scope


def test_signor_refuses_to_invent_required_terms():
    result = draft_agreement(
        AgreementDraftInput(project_id="", title="", scope=""),
        business_id="BIZ-001",
    )
    assert result.agreement is None
    assert len(result.errors) == 3


def test_signor_rejects_invalid_price():
    result = draft_agreement(
        AgreementDraftInput(project_id="PRJ-001", title="Work", scope="Do work", amount="twelve-ish"),
        business_id="BIZ-001",
    )
    assert result.agreement is None
    assert any("valid number" in error for error in result.errors)


def test_signor_web_drafts_and_persists_agreement(monkeypatch):
    import app.signor.web as web_module
    from app.core.memory_store import InMemoryBlackOfficeStore

    store = InMemoryBlackOfficeStore.create()
    monkeypatch.setattr(web_module, "_store", store)
    web_module.app.config["TESTING"] = True
    client = web_module.app.test_client()

    response = client.post(
        "/",
        data={
            "project_id": "PRJ-001",
            "title": "Steel urinal installation",
            "scope": "Install five owner-supplied steel urinals.",
            "amount": "1800.00",
            "currency": "CAD",
            "assumptions": "Mounting surfaces are serviceable.",
            "exclusions": "Wall reconstruction.",
            "payment_terms": "Due on completion.",
            "change_order_terms": "Written approval required.",
        },
    )
    assert response.status_code == 200
    assert b"human confirmation required" in response.data
    agreements = store.agreements.list_for_business("local-development")
    assert len(agreements) == 1
    assert agreements[0].title == "Steel urinal installation"


def test_office_mounts_signor():
    from werkzeug.test import Client
    from werkzeug.wrappers import Response
    from app.office.web import application

    client = Client(application, Response)
    desk = client.get("/")
    assert desk.status_code == 200
    assert b"/signor/" in desk.data
    signor = client.get("/signor/")
    assert signor.status_code == 200
    assert b"Define the agreement" in signor.data
