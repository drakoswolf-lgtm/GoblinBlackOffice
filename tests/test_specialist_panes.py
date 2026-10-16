"""Exercise served art, real project counts, scope and canon identity together."""
from io import BytesIO
from pathlib import Path
from decimal import Decimal

import pytest
from PIL import Image
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.core.runtime import business_id
from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Business, Client as BusinessClient, Project, WorkLog
from app.office import web


PANES = {
    "ledgergut": "LTJG Ledgergut", "signor": "L.CDR SigNor",
    "squarmish": "CPO Squarmish", "packrat": "ENS Packrat",
    "patch": "2PO Patch", "grimsnatch": "LT Grimsnatch",
}


@pytest.fixture
def client(monkeypatch):
    store = InMemoryBlackOfficeStore.create()
    bid = business_id
    store.businesses.save(Business(bid, "Pane QA"))
    store.clients.save(BusinessClient("PANE-CLIENT", bid, "Pane QA"))
    store.projects.save(Project("PANE-ONE", bid, "PANE-CLIENT", "One"))
    store.projects.save(Project("PANE-TWO", bid, "PANE-CLIENT", "Two"))
    store.work_logs.save(WorkLog("PANE-LOG-1", bid, "PANE-ONE", "Frame", Decimal("2")))
    store.work_logs.save(WorkLog("PANE-LOG-2", bid, "PANE-TWO", "Other job", Decimal("5")))
    store.work_logs.save(WorkLog("PANE-LOG-3", "foreign-business", "PANE-ONE", "Foreign", Decimal("9")))
    monkeypatch.setattr(web, "office_store", store)
    return Client(web.application, Response)


def test_panes_and_accessible_identities_are_shared_across_desk_and_project(client):
    for path in ("/", "/jobs/PANE-ONE"):
        response = client.get(path)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert html.count('class="specialist-pane-art"') == 6
        assert 'face-' not in html
        for key, identity in PANES.items():
            assert f'data-specialist="{key}"' in html
            assert f'Specialist: {identity}.' in html
            assert f'/canon/characters/holographic-panes/{key}.png' in html
        assert "Receipt Log" in html and "Invoices &amp; Payments" in html
    desk = client.get("/").get_data(as_text=True)
    assert desk.count('>Workflow guide</span>') == 3
    assert 'href="/workflows/grimscratch"' in desk


def test_project_panels_use_only_records_from_this_project_and_business(client):
    html = client.get("/jobs/PANE-ONE").get_data(as_text=True)
    assert 'id="project-patch-summary">1 work entry</span>' in html
    assert 'id="project-ledgergut-summary">0 expense records</span>' in html
    assert 'href="/ledgergut/?project_id=PANE-ONE"' in html
    assert 'href="/signor/?project_id=PANE-ONE"' in html
    assert 'href="/aeterna/command?project_id=PANE-ONE&amp;view=checks"' in html
    for anchor in ("project-invoices", "packrat-shopping", "project-work"):
        assert f'href="#{anchor}"' in html
        assert f'id="{anchor}"' in html
    assert client.get("/jobs/DOES-NOT-EXIST").status_code == 404


@pytest.mark.parametrize("key", PANES)
def test_every_original_png_is_served_unchanged_and_cache_revalidates(client, key):
    relative = f"characters/holographic-panes/{key}.png"
    response = client.get(f"/canon/{relative}")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    source = Path(web._canon_root) / relative
    assert response.data == source.read_bytes()
    with Image.open(BytesIO(response.data)) as image:
        assert image.size == (1536, 877)
        image.verify()
    assert client.get(f"/canon/{relative}", headers={"If-None-Match": response.headers["ETag"]}).status_code == 304
