from decimal import Decimal

from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Agreement, AgreementStatus, Invoice, InvoiceStatus


def test_signor_confirmation_promotes_draft_to_proposed(monkeypatch):
    import app.signor.web as web
    store = InMemoryBlackOfficeStore.create()
    store.agreements.save(Agreement(agreement_id="AGR-1", business_id="local-development", project_id="PRJ-1", title="Work", scope="Do it"))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    response = web.app.test_client().post("/agreements/AGR-1/confirm")

    assert response.status_code == 302
    confirmed = store.agreements.get("AGR-1", "local-development")
    assert confirmed.status == AgreementStatus.PROPOSED


def test_signor_cannot_reconfirm_non_draft(monkeypatch):
    import app.signor.web as web
    store = InMemoryBlackOfficeStore.create()
    store.agreements.save(Agreement(agreement_id="AGR-1", business_id="local-development", project_id="PRJ-1", title="Work", scope="Do it", status=AgreementStatus.PROPOSED))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    assert web.app.test_client().post("/agreements/AGR-1/confirm").status_code == 409


def test_squarmish_confirmation_promotes_draft_to_approved(monkeypatch):
    import app.squarmish.web as web
    store = InMemoryBlackOfficeStore.create()
    store.invoices.save(Invoice(invoice_id="SQ-1", business_id="local-development", project_id="PRJ-1", client_id="CLI-1", total=Decimal("125.00")))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    response = web.app.test_client().post("/invoices/SQ-1/confirm")

    assert response.status_code == 302
    confirmed = store.invoices.get("SQ-1", "local-development")
    assert confirmed.status == InvoiceStatus.APPROVED


def test_squarmish_cannot_reapprove_non_draft(monkeypatch):
    import app.squarmish.web as web
    store = InMemoryBlackOfficeStore.create()
    store.invoices.save(Invoice(invoice_id="SQ-1", business_id="local-development", project_id="PRJ-1", client_id="CLI-1", total=Decimal("125.00"), status=InvoiceStatus.APPROVED))
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    assert web.app.test_client().post("/invoices/SQ-1/confirm").status_code == 409
