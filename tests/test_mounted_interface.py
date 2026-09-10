from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.office.web import application


def test_shared_interface_stylesheet_is_served():
    client = Client(application, Response)

    response = client.get("/static/gbo.css")

    assert response.status_code == 200
    assert b"--panel" in response.data
    assert b".specialist-card" in response.data


def test_ledgergut_actions_stay_inside_mounted_specialist():
    client = Client(application, Response)

    response = client.get("/ledgergut/")

    assert response.status_code == 200
    assert b'action="/ledgergut/receipts/new"' in response.data
    assert b'formaction="/ledgergut/receipts/scan"' in response.data
    assert b"Save Receipt" in response.data


def test_specialist_pages_share_office_design_system():
    client = Client(application, Response)

    for path in ("/ledgergut/", "/signor/", "/squarmish/"):
        response = client.get(path)
        assert response.status_code == 200
        assert b'href="/static/gbo.css"' in response.data
