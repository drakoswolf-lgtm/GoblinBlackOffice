from fastapi import FastAPI, File, Form, UploadFile

from app.models import ExtractResponse, GenerateRequest, GenerateResponse
from app.services.ocr_service import OcrService
from app.services.reimbursement_service import ReimbursementGeneratorService

app = FastAPI(title='Ledgergut API')
ocr_service = OcrService()
reimbursement_service = ReimbursementGeneratorService()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/ledgergut/extract', response_model=ExtractResponse)
async def extract_receipt(
    file: UploadFile = File(...),
    claimantName: str = Form('Unknown Claimant'),
) -> ExtractResponse:
    image_content = await file.read()
    image_path = await ocr_service.store_image(file.filename, image_content)
    draft = ocr_service.extract_mock(image_path=image_path, claimant_name=claimantName)
    return ExtractResponse(
        draft=draft,
        statusMessages=[
            'Ledgergut is examining the tribute...',
            'Vendor identified.',
            'Total extracted.',
            'Receipt image secured.',
            'Reimbursement package prepared.',
        ],
    )


@app.post('/ledgergut/generate-reimbursement', response_model=GenerateResponse)
def generate_reimbursement(request: GenerateRequest) -> GenerateResponse:
    workbook_path = reimbursement_service.generate(request.draft)
    return GenerateResponse(
        workbookPath=workbook_path,
        receiptEmbedded=True,
        availableActions=['save', 'share', 'export'],
    )
