from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.office.web import application


def test_office_desk_loads() -> None:
    client = Client(application, Response)
    response = client.get("/")

    assert response.status_code == 200
    assert b"Give the paperwork" in response.data
    assert b"Ledgergut" in response.data
    assert b"SigNor" in response.data
    assert b"Squarmish" in response.data


def test_ledgergut_is_mounted_under_office_shell() -> None:
    client = Client(application, Response)
    response = client.get("/ledgergut/")

    assert response.status_code == 200
    assert b"Ledgergut" in response.data
    assert b"Save Receipt" in response.data


def test_office_health_endpoint() -> None:
    client = Client(application, Response)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "goblin-black-office"
