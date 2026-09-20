from app.office.grunts import GRUNT_WORKFLOWS
from app.office.web import office_app


def test_wave2_grunts_are_defined_with_handoffs_and_human_gates():
    assert set(GRUNT_WORKFLOWS) == {"packrat", "patch", "grimscratch"}
    for grunt in GRUNT_WORKFLOWS.values():
        assert len(grunt["stages"]) >= 5
        assert grunt["handoffs"]
        assert grunt["guardrails"]
        assert grunt["first_release"]


def test_office_desk_surfaces_wave2_workflow_rough_ins():
    office_app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)
    response = office_app.test_client().get("/")
    assert response.status_code == 200
    assert b"Packrat McDuffel" in response.data
    assert b"Patch" in response.data
    assert b"Grimscratch" in response.data
    assert b"/workflows/packrat" in response.data


def test_wave2_workflow_pages_render_and_unknown_grunt_404s():
    office_app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)
    client = office_app.test_client()

    packrat = client.get("/workflows/packrat")
    assert packrat.status_code == 200
    assert b"Logistics &amp; materials" in packrat.data
    assert b"Ledgergut" in packrat.data
    assert b"explicit human approval" in packrat.data

    patch = client.get("/workflows/patch")
    assert patch.status_code == 200
    assert b"Operations &amp; work orders" in patch.data
    assert b"Squarmish" in patch.data
    assert b"Never invent labour hours" in patch.data

    grimscratch = client.get("/workflows/grimscratch")
    assert grimscratch.status_code == 200
    assert b"Risk &amp; compliance" in grimscratch.data
    assert b"Advisory by default" in grimscratch.data
    assert b"human accepts, rejects, or overrides" in grimscratch.data

    assert client.get("/workflows/not-a-goblin").status_code == 404
