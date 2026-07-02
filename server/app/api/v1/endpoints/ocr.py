from fastapi import APIRouter

router = APIRouter()


@router.get('/status')
def ocr_status() -> dict[str, str]:
    return {'module': 'ocr', 'status': 'placeholder'}
