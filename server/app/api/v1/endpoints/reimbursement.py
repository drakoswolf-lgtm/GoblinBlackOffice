from fastapi import APIRouter

router = APIRouter()


@router.get('/status')
def reimbursement_status() -> dict[str, str]:
    return {'module': 'reimbursement', 'status': 'placeholder'}
