from pathlib import Path
import uuid

from app.models import ReceiptDraft


class ReimbursementGeneratorService:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path('/tmp/ledgergut_generated')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, draft: ReceiptDraft) -> str:
        output_path = self.output_dir / f'reimbursement-{uuid.uuid4()}.xlsx'
        output_path.write_text(
            '\n'.join(
                [
                    'Ledgergut Reimbursement Stub',
                    f'Vendor: {draft.vendor}',
                    f'Date: {draft.date}',
                    f'Total Paid: {draft.totalPaid}',
                    f'Purchase Group: {draft.purchaseGroup}',
                    f'Claimant Name: {draft.claimantName}',
                    f'Receipt Image Path: {draft.receiptImagePath}',
                ]
            ),
            encoding='utf-8',
        )
        return str(output_path)
