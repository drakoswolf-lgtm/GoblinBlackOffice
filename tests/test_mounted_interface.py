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


def test_canon_asset_library_is_served_by_office_app():
    client = Client(application, Response)

    response = client.get("/canon/brand/canon-app-badge.webp")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")


def test_office_desk_mounts_canonical_splash_runtime():
    client = Client(application, Response)

    response = client.get("/")

    assert response.status_code == 200
    assert b'data-gbo-splash' in response.data
    assert b'gbo-sticky-lines' in response.data
    assert b'/static/gbo.js' in response.data
    assert b'canon-startup-charge.webp' not in response.data


def test_office_desk_mounts_aeterna_advice_with_canon_headshot():
    client = Client(application, Response)

    response = client.get("/")

    assert response.status_code == 200
    assert b'data-aeterna-advice' in response.data
    assert b'/canon/characters/canon-aeterna-headshot.webp' in response.data
    assert b'Cmdr. Aeterna Skyeward' not in response.data
    assert "Cmdr. Æterna Skyeward".encode("utf-8") in response.data


def test_shared_runtime_contains_five_second_minimum_and_door_states():
    client = Client(application, Response)

    response = client.get("/static/gbo.js")

    assert response.status_code == 200
    assert b"const minMs = 5000" in response.data
    assert b"is-breaching" in response.data
    assert b"is-opening" in response.data
    assert b"is-whiteout" in response.data
    assert b"UPDATING" in response.data


def test_curriculum_vitae_mounts_canonical_holographic_briefing():
    client = Client(application, Response)

    response = client.get("/onboarding")

    # Development mode has no authenticated user, so the route redirects.
    assert response.status_code in {200, 302}

    runtime = client.get("/static/curriculum.js")
    assert runtime.status_code == 200
    assert b"data-curriculum" in runtime.data
    assert b"is-speaking" in runtime.data
    assert b"is-leaving-left" in runtime.data
    assert b"data-tax-status" in runtime.data


def test_curriculum_styles_include_holographic_command_layers():
    client = Client(application, Response)

    response = client.get("/static/gbo.css")

    assert response.status_code == 200
    assert b".curriculum-holo" in response.data
    assert b".aeterna-briefing" in response.data
    assert b"@keyframes holo-assemble" in response.data
    assert b"@keyframes aeterna-breathe" in response.data


def test_startup_sequence_is_session_scoped_with_explicit_replay():
    client = Client(application, Response)
    runtime = client.get("/static/gbo.js")
    assert runtime.status_code == 200
    assert b"gbo.startup.seen" in runtime.data
    assert b"sessionStorage" in runtime.data
    assert b"params.get('splash') === '1'" in runtime.data
    assert b"params.get('updating') === '1'" in runtime.data
