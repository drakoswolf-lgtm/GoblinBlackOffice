from app.core.runtime import office_store
from app.office.records import create_client, create_project
from app.office.web import office_app


def test_client_and_project_creation_are_business_scoped():
    client, errors = create_client(business_id="BIZ-SUTURE", name="Thunder Works")
    assert errors == ()
    project, errors = create_project(business_id="BIZ-SUTURE", client_id=client.client_id, name="Roof before rain")
    assert errors == ()
    assert project.client_id == client.client_id
    assert office_store.clients.get(client.client_id, "OTHER-BIZ") is None
    assert office_store.projects.get(project.project_id, "OTHER-BIZ") is None


def test_project_rejects_foreign_or_missing_client():
    project, errors = create_project(business_id="BIZ-NOPE", client_id="CLI-MISSING", name="Nope")
    assert project is None
    assert "Choose a client from this Office." in errors


def test_record_desk_is_available():
    office_app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)
    response = office_app.test_client().get("/records")
    assert response.status_code == 200
    assert b"Clients & Projects" in response.data
