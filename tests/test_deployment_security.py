from app.office.web import office_app


def test_deployment_security_contract_is_documented():
    from pathlib import Path

    text = Path("docs/deployment/digitalocean.md").read_text(encoding="utf-8")
    assert "GBO_AUTH_REQUIRED=1" in text
    assert "GBO_SECRET=<long random secret>" in text
    assert "GBO_INVITE_TOKEN=<private beta invite code>" in text
    assert "same-origin protection" in text
    assert "Health check path: `/health`" in text


def test_cross_site_write_is_rejected(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_SAME_ORIGIN_PROTECTION", True)
    client = office_app.test_client()

    response = client.post(
        "/login",
        data={"email": "nobody@example.test", "password": "not-a-password"},
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 400
    assert b"Cross-site request rejected" in response.data


def test_same_origin_write_is_allowed(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_SAME_ORIGIN_PROTECTION", True)
    client = office_app.test_client()

    response = client.post(
        "/login",
        data={"email": "nobody@example.test", "password": "not-a-password"},
        headers={"Origin": "http://localhost"},
    )

    assert response.status_code == 200
    assert b"Email or password not recognized" in response.data


def test_private_beta_registration_requires_matching_invite(monkeypatch):
    monkeypatch.setitem(office_app.config, "GBO_SAME_ORIGIN_PROTECTION", False)
    monkeypatch.setitem(office_app.config, "GBO_INVITE_TOKEN", "invite-owl-42")
    client = office_app.test_client()

    rejected = client.post(
        "/register",
        data={
            "display_name": "Beta Operator",
            "email": "beta-security-rejected@example.test",
            "password": "correct-horse-battery",
            "invite_code": "wrong-code",
        },
    )
    assert rejected.status_code == 200
    assert b"valid private-beta invite code" in rejected.data

    accepted = client.post(
        "/register",
        data={
            "display_name": "Beta Operator",
            "email": "beta-security-accepted@example.test",
            "password": "correct-horse-battery",
            "invite_code": "invite-owl-42",
        },
    )
    assert accepted.status_code == 302
    assert accepted.headers["Location"].endswith("/onboarding")
