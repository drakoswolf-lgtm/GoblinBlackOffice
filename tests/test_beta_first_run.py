from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.office.web import application, office_app


def test_first_run_can_reach_office_and_open_a_job():
    office_app.config.update(
        TESTING=True,
        GBO_AUTH_REQUIRED=False,
        GBO_INVITE_TOKEN="",
    )
    client = Client(application, Response)

    register = client.post(
        "/register",
        data={
            "email": "beta-first-run@example.com",
            "password": "beta-password-123",
            "display_name": "Beta Commander",
        },
    )
    assert register.status_code == 302
    assert register.headers["Location"].endswith("/onboarding")

    onboarding = client.get("/onboarding")
    assert onboarding.status_code == 200
    assert "CURRICULUM VITÆ".encode("utf-8") in onboarding.data
    assert b"ENTER THE BLACK OFFICE" in onboarding.data

    completed = client.post(
        "/onboarding",
        data={
            "business_name": "Beta Contracting",
            "business_type": "Contracting",
            "currency": "CAD",
            "legal_structure": "Sole proprietorship",
            "operating_model": "Mobile / service-area",
            "country": "Canada",
            "region": "British Columbia",
        },
    )
    assert completed.status_code == 302
    assert completed.headers["Location"].endswith("/")

    desk = client.get("/")
    assert desk.status_code == 200
    assert b"Open a new job" in desk.data

    new_job = client.post(
        "/jobs/new",
        data={
            "client_name": "Beta Client",
            "client_email": "client@example.com",
            "project_name": "64 LF Cedar Fence",
            "description": "Build 64 lineal feet of cedar fencing with one gate.",
        },
    )
    assert new_job.status_code == 302
    assert "/jobs/PRJ-" in new_job.headers["Location"]

    workbench = client.get(new_job.headers["Location"])
    assert workbench.status_code == 200
    assert b"64 LF Cedar Fence" in workbench.data
    assert b"Draft agreement" in workbench.data
