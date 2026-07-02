"""
Integration tests for the Ledgergut standalone router.
"""

import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestLedgergutExtract:
    def test_extract_text_receipt(self):
        receipt = (
            b"Coffee Palace\n"
            b"123 Bean St\n"
            b"Date: 2024-03-15\n"
            b"Latte    $5.50\n"
            b"Total Due $5.50\n"
        )
        res = client.post(
            "/ledgergut/extract",
            files={"file": ("receipt.txt", io.BytesIO(receipt), "text/plain")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["vendor"] == "Coffee Palace"
        assert data["total"] == 5.50
        assert 0.0 <= data["confidence"] <= 1.0

    def test_extract_image_returns_low_confidence(self, tmp_path):
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 20  # minimal JPEG header stub
        res = client.post(
            "/ledgergut/extract",
            files={"file": ("receipt.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["confidence"] < 0.5
        assert len(data["warnings"]) > 0

    def test_extract_missing_file_returns_422(self):
        res = client.post("/ledgergut/extract")
        assert res.status_code == 422


class TestLedgergutGenerate:
    def test_generate_returns_filename_and_path(self):
        res = client.post(
            "/ledgergut/generate-reimbursement",
            json={
                "vendor": "Deli Corp",
                "date": "2024-04-01",
                "total": 8.00,
                "currency": "USD",
                "purpose": "Team lunch",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "filename" in data
        assert data["filename"].startswith("reimbursement_")
        assert data["download_path"].startswith("/ledgergut/download/")

    def test_generate_with_minimal_payload(self):
        res = client.post("/ledgergut/generate-reimbursement", json={})
        assert res.status_code == 200
        data = res.json()
        assert "filename" in data

    def test_download_generated_package(self):
        gen_res = client.post(
            "/ledgergut/generate-reimbursement",
            json={"vendor": "Acme", "date": "2024-01-01", "total": 42.00, "purpose": "Supplies"},
        )
        assert gen_res.status_code == 200
        filename = gen_res.json()["filename"]

        dl_res = client.get(f"/ledgergut/download/{filename}")
        assert dl_res.status_code == 200
        assert b"GOBLIN BLACK OFFICE" in dl_res.content
        assert b"Acme" in dl_res.content

    def test_download_nonexistent_file_returns_404(self):
        res = client.get("/ledgergut/download/nonexistent_file.txt")
        assert res.status_code == 404

    def test_download_path_traversal_is_blocked(self):
        res = client.get("/ledgergut/download/../../../etc/passwd")
        assert res.status_code in (404, 422)
