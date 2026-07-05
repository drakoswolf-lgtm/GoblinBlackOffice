from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.invoice import InvoiceListResponse, InvoiceRead
from app.services.squarmish_service import create_invoice_from_project, get_invoice_or_404, list_invoices

router = APIRouter(prefix="/squarmish", tags=["squarmish"])


@router.post("/invoices/from-project/{project_name}", response_model=InvoiceRead, status_code=201)
def create_project_invoice(project_name: str, db: Session = Depends(get_db)) -> InvoiceRead:
    return create_invoice_from_project(db, project_name)


@router.get("/invoices", response_model=InvoiceListResponse)
def list_squarmish_invoices(db: Session = Depends(get_db)) -> InvoiceListResponse:
    return InvoiceListResponse(invoices=list_invoices(db))


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_squarmish_invoice(invoice_id: str, db: Session = Depends(get_db)) -> InvoiceRead:
    return get_invoice_or_404(db, invoice_id)
