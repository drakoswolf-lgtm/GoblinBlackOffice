"""
Integration tests for the Cases API.
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import store


@pytest.fixture(autouse=True)
def clear_store():
    """Reset in-memory store between tests."""
    store._store.clear()
    yield
    store._store.clear()


client = TestClient(app)


class TestCaseLifecycle:
    def test_create_receipt_case(self):
        res = client.post("/cases", json={"type": "receipt_reimbursement"})
        assert res.status_code == 201
        data = res.json()
        assert data["type"] == "receipt_reimbursement"
        assert data["status"] == "intake"
        assert data["assignedGoblinId"] == "ledgergut"

    def test_list_cases(self):
        client.post("/cases", json={"type": "receipt_reimbursement"})
        client.post("/cases", json={"type": "receipt_reimbursement"})
        res = client.get("/cases")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_get_case_not_found(self):
        res = client.get("/cases/nonexistent")
        assert res.status_code == 404

    def test_upload_evidence_and_extract(self, tmp_path):
        # Create case
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]

        # Upload a text receipt
        receipt_text = (
            "Coffee Palace\n123 Bean St\n"
            "Date: 2024-03-15\n"
            "Latte    $5.50\n"
            "Total Due $5.50\n"
        )
        res = client.post(
            f"/cases/{case_id}/evidence",
            files={"files": ("receipt.txt", io.BytesIO(receipt_text.encode()), "text/plain")},
        )
        assert res.status_code == 200
        assert len(res.json()["evidenceFiles"]) == 1

        # Run extraction
        res = client.post(f"/cases/{case_id}/extract")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "review"
        assert data["extractedData"]["vendor"] == "Coffee Palace"
        assert data["extractedData"]["total"] == 5.50

    def test_cannot_extract_without_evidence(self):
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]
        res = client.post(f"/cases/{case_id}/extract")
        assert res.status_code == 400

    def test_review_and_generate(self, tmp_path):
        # Full workflow
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]

        receipt_text = "Deli Corp\n2024-04-01\nSandwich $8.00\nTotal $8.00\n"
        client.post(
            f"/cases/{case_id}/evidence",
            files={"files": ("r.txt", io.BytesIO(receipt_text.encode()), "text/plain")},
        )
        client.post(f"/cases/{case_id}/extract")

        # Save review
        res = client.put(
            f"/cases/{case_id}/review",
            json={
                "vendor": "Deli Corp",
                "date": "2024-04-01",
                "total": 8.00,
                "purpose": "Team lunch",
                "approved": True,
            },
        )
        assert res.status_code == 200
        assert res.json()["reviewedData"]["approved"] is True

        # Generate package
        res = client.post(f"/cases/{case_id}/generate")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completion"
        assert len(data["outputFiles"]) == 1

    def test_generate_blocked_without_approval(self):
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]

        receipt_text = "Shop\n2024-01-01\nTotal $5.00\n"
        client.post(
            f"/cases/{case_id}/evidence",
            files={"files": ("r.txt", io.BytesIO(receipt_text.encode()), "text/plain")},
        )
        client.post(f"/cases/{case_id}/extract")
        client.put(f"/cases/{case_id}/review", json={"approved": False})

        res = client.post(f"/cases/{case_id}/generate")
        assert res.status_code == 400

    def test_archive(self):
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]

        receipt_text = "Bookstore\n2024-06-01\nTotal $12.00\n"
        client.post(
            f"/cases/{case_id}/evidence",
            files={"files": ("r.txt", io.BytesIO(receipt_text.encode()), "text/plain")},
        )
        client.post(f"/cases/{case_id}/extract")
        client.put(
            f"/cases/{case_id}/review",
            json={"vendor": "Bookstore", "total": 12.0, "purpose": "Books", "approved": True},
        )
        client.post(f"/cases/{case_id}/generate")

        res = client.post(f"/cases/{case_id}/archive")
        assert res.status_code == 200
        assert res.json()["status"] == "archived"

    def test_delete_case(self):
        case_id = client.post(
            "/cases", json={"type": "receipt_reimbursement"}
        ).json()["id"]
        res = client.delete(f"/cases/{case_id}")
        assert res.status_code == 204
        res = client.get(f"/cases/{case_id}")
        assert res.status_code == 404


class TestGoblinsAPI:
    def test_list_goblins(self):
        res = client.get("/goblins")
        assert res.status_code == 200
        goblins = res.json()
        assert any(g["id"] == "ledgergut" for g in goblins)

    def test_get_ledgergut(self):
        res = client.get("/goblins/ledgergut")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Ledgergut"
        assert data["division"] == "finance"

    def test_get_unknown_goblin(self):
        res = client.get("/goblins/unknown")
        assert res.status_code == 404
