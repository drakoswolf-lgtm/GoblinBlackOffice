"""
Case (Operation) model — the universal unit of work for every goblin operative.

Fields are designed to be inherited by all future case types.
Ledgergut's receipt_reimbursement is the reference implementation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class CaseType(str, Enum):
    RECEIPT_REIMBURSEMENT = "receipt_reimbursement"
    # Future goblins register their types here:
    # CONTRACT_REVIEW = "contract_review"
    # INVOICE_PROCESSING = "invoice_processing"


class CaseStatus(str, Enum):
    """Canonical workflow stages shared by all goblins."""

    INTAKE = "intake"
    EXTRACTION = "extraction"
    REVIEW = "review"
    GENERATION = "generation"
    COMPLETION = "completion"
    ARCHIVED = "archived"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ExtractedData(BaseModel):
    """Raw output from the goblin's extraction engine."""

    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    currency: str = "USD"
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    raw_text: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)


class ReviewedData(BaseModel):
    """User-edited fields that override or confirm extracted data."""

    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    currency: Optional[str] = "USD"
    purpose: Optional[str] = None
    notes: Optional[str] = None
    approved: bool = False


# ---------------------------------------------------------------------------
# Request / Response shapes
# ---------------------------------------------------------------------------


class CaseCreate(BaseModel):
    type: CaseType
    assignedGoblinId: Optional[str] = None


class CaseReviewUpdate(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    currency: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    approved: bool = False


# ---------------------------------------------------------------------------
# Core Case model (in-memory store uses this as its record type)
# ---------------------------------------------------------------------------


class Case(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: CaseType
    assignedGoblinId: Optional[str] = None
    status: CaseStatus = CaseStatus.INTAKE
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Files
    evidenceFiles: List[str] = Field(default_factory=list)
    outputFiles: List[str] = Field(default_factory=list)

    # Data lifecycle
    extractedData: Optional[ExtractedData] = None
    reviewedData: Optional[ReviewedData] = None

    # Summary metrics (mirrors extractedData, updated on extraction)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)

    # Human-readable status detail
    statusMessage: str = "Awaiting evidence submission."

    def touch(self) -> None:
        self.updatedAt = datetime.now(timezone.utc)
