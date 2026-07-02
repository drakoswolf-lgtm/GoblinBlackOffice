from pathlib import Path
import uuid

from app.models import ConfidenceFlags, ReceiptDraft


class OcrService:
    def __init__(self, upload_dir: Path | None = None) -> None:
        self.upload_dir = upload_dir or Path('/tmp/ledgergut_uploads')
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def store_image(self, file_name: str, content: bytes) -> str:
        suffix = Path(file_name).suffix or '.jpg'
        file_path = self.upload_dir / f'{uuid.uuid4()}{suffix}'
        file_path.write_bytes(content)
        return str(file_path)

    def extract_mock(self, image_path: str, claimant_name: str) -> ReceiptDraft:
        return ReceiptDraft(
            vendor='Goblin Supply Co.',
            date='2026-07-02',
            totalPaid=42.50,
            purchaseGroup='Materials',
            claimantName=claimant_name,
            receiptImagePath=image_path,
            confidenceFlags=ConfidenceFlags(vendor=0.96, date=0.92, totalPaid=0.94),
        )
