from decimal import Decimal

from app.core.documents import build_agreement_pdf, build_invoice_pdf
from app.core.memory_store import InMemoryBlackOfficeStore
from app.core.models import Agreement, Business, Client, Invoice, InvoiceLineItem, Project


def _records():
    business = Business(business_id="local-development", name="Forge Contracting")
    client = Client(client_id="CLI-1", business_id="local-development", name="Alexander Hotel")
    project = Project(project_id="PRJ-1", business_id="local-development", client_id="CLI-1", name="Front Desk")
    agreement = Agreement(
        agreement_id="AGR-1",
        business_id="local-development",
        project_id="PRJ-1",
        title="Reception desk finishing",
        scope="Finish tile and trim.\nAdditional work requires written approval.",
        amount=Decimal("1250.00"),
    )
    invoice = Invoice(
        invoice_id="SQ-1",
        business_id="local-development",
        project_id="PRJ-1",
        client_id="CLI-1",
        total=Decimal("1278.50"),
        subtotal=Decimal("1278.50"),
        agreement_id="AGR-1",
        line_items=(
            InvoiceLineItem(description="Reception desk finishing", amount=Decimal("1250.00"), source_type="agreement", source_id="AGR-1"),
            InvoiceLineItem(description="Fasteners", amount=Decimal("28.50"), source_type="expense", source_id="EXP-1"),
        ),
        review_notes=("Tax has not been applied.",),
    )
    return business, client, project, agreement, invoice


def test_agreement_renderer_returns_pdf_bytes():
    business, client, project, agreement, _ = _records()
    pdf = build_agreement_pdf(business=business, agreement=agreement, project=project, client=client)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_invoice_renderer_returns_pdf_bytes():
    business, client, project, _, invoice = _records()
    pdf = build_invoice_pdf(business=business, invoice=invoice, project=project, client=client)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_signor_pdf_endpoint_is_tenant_scoped(monkeypatch):
    import app.signor.web as web
    business, client, project, agreement, _ = _records()
    store = InMemoryBlackOfficeStore.create()
    store.businesses.save(business)
    store.clients.save(client)
    store.projects.save(project)
    store.agreements.save(agreement)
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    response = web.app.test_client().get("/agreements/AGR-1/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "attachment" in response.headers["Content-Disposition"]


def test_squarmish_pdf_endpoint_uses_persisted_invoice(monkeypatch):
    import app.squarmish.web as web
    business, client, project, _, invoice = _records()
    store = InMemoryBlackOfficeStore.create()
    store.businesses.save(business)
    store.clients.save(client)
    store.projects.save(project)
    store.invoices.save(invoice)
    monkeypatch.setattr(web, "_store", store)
    web.app.config.update(TESTING=True, GBO_AUTH_REQUIRED=False)

    response = web.app.test_client().get("/invoices/SQ-1/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "attachment" in response.headers["Content-Disposition"]
