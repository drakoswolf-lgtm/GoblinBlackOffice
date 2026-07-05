from decimal import Decimal


def test_can_generate_squarmish_invoice_draft_from_project(client):
    response = client.post("/api/v1/squarmish/invoices/from-project/Skylight")

    assert response.status_code == 201
    body = response.json()
    assert body["project_name"] == "Skylight"
    assert any(line["linked_record_id"] == "LG-20260703-0001" for line in body["line_items"])
    assert Decimal(body["subtotal"]) == Decimal("49.18")
    assert Decimal(body["tax_amount"]) == Decimal("5.90")


def test_already_invoiced_receipts_are_not_duplicated(client):
    first_response = client.post("/api/v1/squarmish/invoices/from-project/Skylight")
    second_response = client.post("/api/v1/squarmish/invoices/from-project/Skylight")

    assert first_response.status_code == 201
    assert second_response.status_code == 404


def test_invoice_generated_from_maybe_billable_receipts_is_marked_needs_user_review(client):
    response = client.post("/api/v1/squarmish/invoices/from-project/Skylight")

    assert response.status_code == 201
    body = response.json()
    assert body["needs_user_review"] is True
    assert body["status"] == "pending_review"
    assert "maybe_billable" in (body["review_notes"] or "")
