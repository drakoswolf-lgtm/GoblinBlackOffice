from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.receipt import ReceiptCreate, ReceiptListResponse, ReceiptRead, ReceiptUpdate
from app.services.ledgergut_service import create_receipt, get_receipt_or_404, list_receipts, update_receipt

router = APIRouter(prefix="/ledgergut", tags=["ledgergut"])


@router.post("/receipts", response_model=ReceiptRead, status_code=201)
def create_ledgergut_receipt(payload: ReceiptCreate, db: Session = Depends(get_db)) -> ReceiptRead:
    return create_receipt(db, payload)


@router.get("/receipts", response_model=ReceiptListResponse)
def list_ledgergut_receipts(db: Session = Depends(get_db)) -> ReceiptListResponse:
    return ReceiptListResponse(receipts=list_receipts(db))


@router.get("/receipts/{record_id}", response_model=ReceiptRead)
def get_ledgergut_receipt(record_id: str, db: Session = Depends(get_db)) -> ReceiptRead:
    return get_receipt_or_404(db, record_id)


@router.patch("/receipts/{record_id}", response_model=ReceiptRead)
def patch_ledgergut_receipt(
    record_id: str,
    payload: ReceiptUpdate,
    db: Session = Depends(get_db),
) -> ReceiptRead:
    return update_receipt(db, record_id, payload)
