from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Agreement, Client, Project


def test_signor_lists_human_project_names(monkeypatch):
    import app.signor.web as web
    store = InMemoryBlackOfficeStore.create()
    store.clients.save(Client(client_id="CLI-1", business_id="local-development", name="Alexander Hotel"))
    store.projects.save(Project(project_id="PRJ-1", business_id="local-development", client_id="CLI-1", name="Front Desk"))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)
    response = web.app.test_client().get("/")
    assert response.status_code == 200
    assert b"Front Desk" in response.data
    assert b"Alexander Hotel" in response.data
    assert b"Project ID" not in response.data


def test_squarmish_infers_client_from_agreement_project(monkeypatch):
    import app.squarmish.web as web
    store = InMemoryBlackOfficeStore.create()
    store.clients.save(Client(client_id="CLI-1", business_id="local-development", name="Alexander Hotel"))
    store.projects.save(Project(project_id="PRJ-1", business_id="local-development", client_id="CLI-1", name="Front Desk"))
    store.agreements.save(Agreement(agreement_id="AGR-1", business_id="local-development", project_id="PRJ-1", title="Finish desk", scope="Finish it"))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)
    response = web.app.test_client().post("/", data={"agreement_id":"AGR-1","include_agreement_amount":"1"})
    assert response.status_code == 200
    assert b"Client ID" not in response.data
    assert b"Alexander Hotel" in response.data
