from app.models import ConfidenceFlags, ReceiptDraft


def test_receipt_draft_serialization() -> None:
    draft = ReceiptDraft(
        vendor='Goblin Supply Co.',
        date='2026-07-02',
        totalPaid=42.5,
        purchaseGroup='Materials',
        claimantName='Glim',
        receiptImagePath='/tmp/receipt.jpg',
        confidenceFlags=ConfidenceFlags(vendor=0.9, date=0.8, totalPaid=0.95),
    )

    payload = draft.model_dump()
    restored = ReceiptDraft.model_validate(payload)

    assert restored.vendor == 'Goblin Supply Co.'
    assert restored.claimantName == 'Glim'
    assert restored.confidenceFlags.totalPaid == 0.95
