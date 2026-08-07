"""Tests for PWA infrastructure, authentication, security headers, and environment config."""

from __future__ import annotations

import io
import importlib
import json
import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Test-fixture credentials (not real secrets — used only in unit tests)
# ---------------------------------------------------------------------------

_FIXTURE_USER = "alice"
_FIXTURE_PASS = "fixture-test-pw"  # noqa: S105 — test-only value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app(
    tmp_path: Path,
    monkeypatch,
    *,
    user: str = "",
    pw: str = "",
):
    """Return a configured Flask test client.

    Auth is active only when user/pw are non-empty.
    LEDGERGUT_ENV is left unset (dev) so _require_env does not raise.
    """
    import app.ledgergut.web as web_module

    monkeypatch.setenv("LEDGERGUT_SECRET", "test-secret")
    monkeypatch.setenv("LEDGERGUT_USERNAME", user)
    monkeypatch.setenv("LEDGERGUT_PASSWORD", pw)
    monkeypatch.delenv("LEDGERGUT_ENV", raising=False)

    # Reload so module-level auth vars pick up the new env
    importlib.reload(web_module)

    from app.ledgergut.storage import ReceiptStore

    store = ReceiptStore(
        store_path=tmp_path / "receipts.json",
        image_dir=tmp_path / "images",
    )
    monkeypatch.setattr(web_module, "_store", store)
    web_module.app.config["TESTING"] = True
    web_module.app.config["LEDGERGUT_PENDING_IMAGES"] = {}
    return web_module.app.test_client(), store


def _basic_auth(user: str, pw: str) -> dict[str, str]:
    import base64

    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _valid_form(**overrides) -> dict[str, str]:
    base: dict[str, str] = {
        "vendor_name": "Home Hardware",
        "receipt_date": "2026-07-01",
        "description": "Materials for site",
        "project_name": "Jackson Retail",
        "expense_category": "materials",
        "subtotal": "25.00",
        "tax_amount": "3.00",
        "total_amount": "28.00",
        "currency": "CAD",
        "paid_by": "steve",
        "reimbursement_status": "not_reimbursed",
        "billable_status": "billable",
        "submitted_by": "testuser",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# /health — unauthenticated
# ---------------------------------------------------------------------------


def test_health_returns_200_without_auth(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_returns_ok_json(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/health")
    data = json.loads(resp.data)
    assert data == {"status": "ok"}


def test_health_does_not_expose_internals(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    body = client.get("/health").data.decode()
    for forbidden in ("receipt", "path", "secret", "username", "runtime", "data"):
        assert forbidden not in body.lower(), f"Health endpoint exposed: {forbidden!r}"


# ---------------------------------------------------------------------------
# Manifest and service worker — unauthenticated
# ---------------------------------------------------------------------------


def test_manifest_accessible_without_auth(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.get("/manifest.json")
    assert resp.status_code == 200


def test_manifest_content_type(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/manifest.json")
    assert "json" in resp.content_type


def test_service_worker_accessible_without_auth(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.get("/sw.js")
    assert resp.status_code == 200


def test_service_worker_has_no_cache_header(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/sw.js")
    assert "no-cache" in resp.headers.get("Cache-Control", "")


def test_service_worker_has_scope_header(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/sw.js")
    assert resp.headers.get("Service-Worker-Allowed") == "/"


# ---------------------------------------------------------------------------
# Service worker content — static allowlist, never caches receipt pages
# ---------------------------------------------------------------------------


def test_sw_does_not_precache_root(tmp_path, monkeypatch):
    import re

    client, _ = _make_app(tmp_path, monkeypatch)
    sw_text = client.get("/sw.js").data.decode()
    assert "STATIC_ALLOWLIST" in sw_text
    match = re.search(r"STATIC_ALLOWLIST\s*=\s*\[([^\]]*)\]", sw_text, re.DOTALL)
    assert match, "STATIC_ALLOWLIST array not found in sw.js"
    allowlist_body = match.group(1)
    # '/' alone must not appear as a cacheable entry
    assert "'/'" not in allowlist_body


def test_sw_allowlist_contains_static_assets(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    sw_text = client.get("/sw.js").data.decode()
    assert "/manifest.json" in sw_text
    assert "/static/icons/icon-192.png" in sw_text
    assert "/static/icons/icon-512.png" in sw_text


def test_sw_does_not_cache_arbitrary_gets(tmp_path, monkeypatch):
    """The SW must not blindly cache all GET responses."""
    client, _ = _make_app(tmp_path, monkeypatch)
    sw_text = client.get("/sw.js").data.decode()
    assert "cache.put(event.request" not in sw_text


def test_sw_does_not_reference_export_route(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    sw_text = client.get("/sw.js").data.decode()
    assert "/export" not in sw_text


# ---------------------------------------------------------------------------
# Authentication — protected routes require credentials
# ---------------------------------------------------------------------------


PROTECTED_ROUTES = [
    ("GET", "/"),
    ("POST", "/receipts/scan"),
    ("POST", "/receipts/new"),
    ("GET", "/export/csv"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_requires_auth(tmp_path, monkeypatch, method, path):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.open(path, method=method)
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_accepts_correct_credentials(tmp_path, monkeypatch, method, path):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    headers = _basic_auth(_FIXTURE_USER, _FIXTURE_PASS)
    data = _valid_form() if method == "POST" else None
    resp = client.open(path, method=method, headers=headers, data=data)
    assert resp.status_code != 401


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_wrong_password(tmp_path, monkeypatch, method, path):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    headers = _basic_auth(_FIXTURE_USER, "wrong-pw")
    resp = client.open(path, method=method, headers=headers)
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_wrong_username(tmp_path, monkeypatch, method, path):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    headers = _basic_auth("mallory", _FIXTURE_PASS)
    resp = client.open(path, method=method, headers=headers)
    assert resp.status_code == 401


def test_auth_challenge_does_not_reveal_which_field_was_wrong(tmp_path, monkeypatch):
    """The 401 body must be identical for bad username vs. bad password."""
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp_bad_user = client.get("/", headers=_basic_auth("eve", _FIXTURE_PASS))
    resp_bad_pass = client.get("/", headers=_basic_auth(_FIXTURE_USER, "wrong-pw"))
    assert resp_bad_user.status_code == resp_bad_pass.status_code == 401
    assert resp_bad_user.data == resp_bad_pass.data


def test_no_auth_configured_allows_all_requests(tmp_path, monkeypatch):
    """When USERNAME and PASSWORD are empty (dev), requests pass without auth."""
    client, _ = _make_app(tmp_path, monkeypatch, user="", pw="")
    resp = client.get("/")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Secure cookie configuration
# ---------------------------------------------------------------------------


def test_session_cookie_secure_is_true(tmp_path, monkeypatch):
    _make_app(tmp_path, monkeypatch)
    import app.ledgergut.web as web_module

    assert web_module.app.config["SESSION_COOKIE_SECURE"] is True


def test_session_cookie_httponly_is_true(tmp_path, monkeypatch):
    _make_app(tmp_path, monkeypatch)
    import app.ledgergut.web as web_module

    assert web_module.app.config["SESSION_COOKIE_HTTPONLY"] is True


def test_session_cookie_samesite_is_lax(tmp_path, monkeypatch):
    _make_app(tmp_path, monkeypatch)
    import app.ledgergut.web as web_module

    assert web_module.app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


# ---------------------------------------------------------------------------
# Cache-Control: no-store on all receipt-bearing responses
# ---------------------------------------------------------------------------


def test_index_has_no_store_header(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/")
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_index_has_private_in_cache_control(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/")
    assert "private" in resp.headers.get("Cache-Control", "")


def test_csv_export_has_no_store_header(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.get("/export/csv")
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_scan_receipt_response_has_no_store(tmp_path, monkeypatch):
    import app.ledgergut.web as web_module

    client, _ = _make_app(tmp_path, monkeypatch)
    monkeypatch.setattr(web_module, "extract_text_from_image", lambda _: "RECEIPT")
    resp = client.post(
        "/receipts/scan",
        data={**_valid_form(), "receipt_image": (io.BytesIO(b"\x89PNG\r\n"), "r.png")},
        content_type="multipart/form-data",
    )
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_new_receipt_error_response_has_no_store(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch)
    resp = client.post("/receipts/new", data=_valid_form(total_amount="0.00"))
    assert "no-store" in resp.headers.get("Cache-Control", "")


# ---------------------------------------------------------------------------
# Production env-var enforcement
# ---------------------------------------------------------------------------


def test_production_mode_requires_secret(tmp_path, monkeypatch):
    import app.ledgergut.web as web_module

    monkeypatch.setenv("LEDGERGUT_ENV", "production")
    monkeypatch.delenv("LEDGERGUT_SECRET", raising=False)
    monkeypatch.setenv("LEDGERGUT_USERNAME", "u")
    monkeypatch.setenv("LEDGERGUT_PASSWORD", "p")

    with pytest.raises(RuntimeError, match="LEDGERGUT_SECRET"):
        importlib.reload(web_module)


def test_production_mode_requires_username(tmp_path, monkeypatch):
    import app.ledgergut.web as web_module

    monkeypatch.setenv("LEDGERGUT_ENV", "production")
    monkeypatch.setenv("LEDGERGUT_SECRET", "s")
    monkeypatch.delenv("LEDGERGUT_USERNAME", raising=False)
    monkeypatch.setenv("LEDGERGUT_PASSWORD", "p")

    with pytest.raises(RuntimeError, match="LEDGERGUT_USERNAME"):
        importlib.reload(web_module)


def test_production_mode_requires_password(tmp_path, monkeypatch):
    import app.ledgergut.web as web_module

    monkeypatch.setenv("LEDGERGUT_ENV", "production")
    monkeypatch.setenv("LEDGERGUT_SECRET", "s")
    monkeypatch.setenv("LEDGERGUT_USERNAME", "u")
    monkeypatch.delenv("LEDGERGUT_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="LEDGERGUT_PASSWORD"):
        importlib.reload(web_module)


def test_dev_mode_allows_missing_secret(tmp_path, monkeypatch):
    import app.ledgergut.web as web_module

    monkeypatch.delenv("LEDGERGUT_ENV", raising=False)
    monkeypatch.delenv("LEDGERGUT_SECRET", raising=False)
    monkeypatch.delenv("LEDGERGUT_USERNAME", raising=False)
    monkeypatch.delenv("LEDGERGUT_PASSWORD", raising=False)

    # Should not raise in dev mode
    importlib.reload(web_module)


# ---------------------------------------------------------------------------
# LEDGERGUT_RUNTIME env var controls storage root
# ---------------------------------------------------------------------------


def test_storage_runtime_env_var_controls_data_root(tmp_path, monkeypatch):
    from app.ledgergut.storage import _default_store, _default_image_dir

    custom = str(tmp_path / "custom_data")
    monkeypatch.setenv("LEDGERGUT_RUNTIME", custom)

    store_path = _default_store()
    image_path = _default_image_dir()

    assert str(store_path).startswith(custom)
    assert str(image_path).startswith(custom)


def test_storage_falls_back_to_runtime_dir_without_env_var(monkeypatch):
    from app.ledgergut.storage import _default_store, _default_image_dir

    monkeypatch.delenv("LEDGERGUT_RUNTIME", raising=False)

    assert "runtime" in str(_default_store())
    assert "runtime" in str(_default_image_dir())


# ---------------------------------------------------------------------------
# CSV export — auth + no-store (integration)
# ---------------------------------------------------------------------------


def test_csv_export_requires_auth_when_configured(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.get("/export/csv")
    assert resp.status_code == 401


def test_csv_export_succeeds_with_auth(tmp_path, monkeypatch):
    client, _ = _make_app(tmp_path, monkeypatch, user=_FIXTURE_USER, pw=_FIXTURE_PASS)
    resp = client.get("/export/csv", headers=_basic_auth(_FIXTURE_USER, _FIXTURE_PASS))
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type
    assert "no-store" in resp.headers.get("Cache-Control", "")
