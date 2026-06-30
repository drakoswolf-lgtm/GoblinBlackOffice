from fastapi import FastAPI

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.ocr import router as ocr_router
from app.api.v1.endpoints.orchestration import router as orchestration_router
from app.api.v1.endpoints.reimbursement import router as reimbursement_router

app = FastAPI(title='Goblin Black Office API', version='0.1.0')

app.include_router(health_router, prefix='/api/v1', tags=['health'])
app.include_router(ocr_router, prefix='/api/v1/ocr', tags=['ocr'])
app.include_router(reimbursement_router, prefix='/api/v1/reimbursements', tags=['reimbursement'])
app.include_router(orchestration_router, prefix='/api/v1/orchestration', tags=['orchestration'])
