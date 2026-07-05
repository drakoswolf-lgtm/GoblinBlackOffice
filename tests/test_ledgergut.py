from decimal import Decimal


def test_can_create_receipt(client):
    payload = {
        "vendor_name": "Princess Auto",
        "vendor_location": "Vancouver, BC",
        "receipt_date": "2026-07-04",
        "project_name": "Skylight",
        "paid_by": "steve",
        "payment_method": "cash",
        "expense_category": "materials",
        "subtotal": "10.00",
        "tax_amount": "1.20",
        "printed_total_amount": "11.20",
        "cash_rounding_adjustment": "0.00",
        "actual_paid_amount": "11.20",
        "cash_tendered": "20.00",
        "change_due": "8.80",
        "currency": "CAD",
        "tax_region": "BC",
        "billable_status": "billable",
        "reimbursement_status": "not_reimbursed",
        "line_items": [
            {
                "sku": "A1",
                "description": "Bolt",
                "quantity": "2",
                "unit_price": "5.00",
                "amount": "10.00",
            }
        ],
        "tax_lines": [
            {"label": "GST", "rate": "0.05", "amount": "0.50"},
            {"label": "PST", "rate": "0.07", "amount": "0.70"},
        ],
    }

    response = client.post("/api/v1/ledgergut/receipts", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["vendor_name"] == "Princess Auto"
    assert body["project_name"] == "Skylight"
    assert body["line_items"][0]["description"] == "Bolt"


def test_can_list_receipts(client):
    response = client.get("/api/v1/ledgergut/receipts")

    assert response.status_code == 200
    receipts = response.json()["receipts"]
    assert len(receipts) >= 2
    assert any(receipt["vendor_name"] == "Home Depot" for receipt in receipts)


def test_can_retrieve_one_receipt(client):
    receipts = client.get("/api/v1/ledgergut/receipts").json()["receipts"]
    record_id = receipts[0]["record_id"]

    response = client.get(f"/api/v1/ledgergut/receipts/{record_id}")

    assert response.status_code == 200
    assert response.json()["record_id"] == record_id


def test_cash_rounding_does_not_break_validation(client):
    receipt = client.get("/api/v1/ledgergut/receipts/LG-20260703-0001").json()

    assert receipt["printed_total_amount"] == "55.08"
    assert receipt["actual_paid_amount"] == "55.05"
    assert receipt["needs_user_review"] is True
    assert "Cash rounding and actual paid amount are inconsistent." not in (receipt["review_notes"] or "")


def test_change_due_is_not_treated_as_total(client):
    receipt = client.get("/api/v1/ledgergut/receipts/LG-20260703-0002").json()

    printed_total = Decimal(receipt["printed_total_amount"])
    change_due = Decimal(receipt["change_due"])
    assert printed_total != change_due
    assert printed_total == Decimal("54.87")
