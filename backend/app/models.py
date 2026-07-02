from pydantic import BaseModel, Field


class ConfidenceFlags(BaseModel):
    vendor: float = Field(ge=0, le=1)
    date: float = Field(ge=0, le=1)
    totalPaid: float = Field(ge=0, le=1)


class ReceiptDraft(BaseModel):
    vendor: str
    date: str
    totalPaid: float
    purchaseGroup: str
    claimantName: str
    receiptImagePath: str
    confidenceFlags: ConfidenceFlags


class ExtractResponse(BaseModel):
    draft: ReceiptDraft
    statusMessages: list[str]


class GenerateRequest(BaseModel):
    draft: ReceiptDraft


class GenerateResponse(BaseModel):
    workbookPath: str
    receiptEmbedded: bool
    availableActions: list[str]
