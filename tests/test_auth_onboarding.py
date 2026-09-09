from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.core.runtime import office_store
from app.ledgergut.web import app as ledgergut_app
from app.office.web import application, office_app
from app.signor.web import app as signor_app
from app.squarmish.web import app as squarmish_app


def test_account_onboarding_and_specialist_access(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", True)
    monkeypatch.setitem(ledgergut_app.config, "GBO_AUTH_REQUIRED", True)
    monkeypatch.setitem(signor_app.config, "GBO_AUTH_REQUIRED", True)
    monkeypatch.setitem(squarmish_app.config, "GBO_AUTH_REQUIRED", True)

    client = Client(application, Response, use_cookies=True)

    locked = client.get("/")
    assert locked.status_code == 302
    assert "/login" in locked.headers["Location"]

    registered = client.post(
        "/register",
        data={"display_name": "Test Operator", "email": "operator@example.test", "password": "correct-horse-battery"},
    )
    assert registered.status_code == 302
    assert registered.headers["Location"].endswith("/onboarding")

    onboarded = client.post(
        "/onboarding",
        data={"business_name": "Test Forge Contracting", "currency": "CAD"},
    )
    assert onboarded.status_code == 302
    assert onboarded.headers["Location"].endswith("/")

    desk = client.get("/")
    assert desk.status_code == 200
    signor = client.get("/signor/")
    assert signor.status_code == 200
    squarmish = client.get("/squarmish/")
    assert squarmish.status_code == 200
    ledgergut = client.get("/ledgergut/")
    assert ledgergut.status_code == 200

    users = [u for u in office_store.users.list_for_business(next(iter([u.business_id for u in office_store.users._records.values() if u.email == "operator@example.test"]))) if u.email == "operator@example.test"] if hasattr(office_store.users, "_records") else []
    if users:
        assert users[0].onboarding_complete is True
        business = office_store.businesses.get(users[0].business_id, users[0].business_id)
        assert business is not None
        assert business.name == "Test Forge Contracting"
        assert business.reporting_currency == "CAD"


def test_registration_rejects_weak_password(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_AUTH_REQUIRED", True)
    client = office_app.test_client()
    response = client.post(
        "/register",
        data={"display_name": "Operator", "email": "weak@example.test", "password": "short"},
    )
    assert response.status_code == 200
    assert b"at least 10 characters" in response.data
