"""Canonical physical Black Office image plates must load unmodified."""
import hashlib
from io import BytesIO
from PIL import Image
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.office.web import application


EXPECTED_PLATES = {
    "desktop": (
        (1586, 992),
        "2995be146bc0b8aaa6b973c04b5c7c31cdd2cbd6c6df1677953f854485f66aa1",
    ),
    "mobile": (
        (941, 1672),
        "81c5dee12db7a09366dd661dfce573dc3873f9ed6a3f7e8364359becf41a645b",
    ),
}


def test_approved_backgrounds_are_served_with_exact_pixels():
    client = Client(application, Response)
    for variant, (dimensions, sha256) in EXPECTED_PLATES.items():
        route = f"/canon/environments/canon-black-office-{variant}.webp"
        response = client.get(route)
        assert response.status_code == 200, f"Approved {variant} background absent: {route}"
        assert response.headers["Content-Type"].startswith("image/webp")
        assert hashlib.sha256(response.data).hexdigest() == sha256, variant
        with Image.open(BytesIO(response.data)) as image:
            assert image.format == "WEBP"
            assert image.size == dimensions
            image.verify()


def test_css_uses_desktop_and_mobile_canon_backgrounds():
    client = Client(application, Response)
    css = client.get("/static/gbo.css")
    assert css.status_code == 200
    assert b'canon-black-office-desktop.webp' in css.data
    assert b'canon-black-office-mobile.webp' in css.data
    assert b'@media (max-width: 700px)' in css.data
    assert b'.command-aeterna { grid-row: 1; }' in css.data
