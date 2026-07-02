from fastapi import APIRouter

router = APIRouter()


@router.get('/status')
def orchestration_status() -> dict[str, str]:
    return {'module': 'orchestration', 'status': 'placeholder'}
