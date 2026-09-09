def test_deployment_security_contract_is_documented():
    from pathlib import Path

    text = Path("docs/deployment/digitalocean.md").read_text(encoding="utf-8")
    assert "GBO_AUTH_REQUIRED=1" in text
    assert "GBO_SECRET=<long random secret>" in text
    assert "Health check path: `/health`" in text
