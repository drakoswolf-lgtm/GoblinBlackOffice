"""
Tests for the core Case and Goblin models.
"""

from datetime import timezone

from app.models.case import (
    Case,
    CaseCreate,
    CaseReviewUpdate,
    CaseStatus,
    CaseType,
    ExtractedData,
    ReviewedData,
)
from app.models.goblin import Goblin, GoblinDivision, GoblinStatus, GOBLIN_BY_ID


class TestCaseModel:
    def test_defaults(self):
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        assert case.status == CaseStatus.INTAKE
        assert case.evidenceFiles == []
        assert case.outputFiles == []
        assert case.extractedData is None
        assert case.reviewedData is None
        assert case.confidence == 0.0
        assert case.warnings == []

    def test_id_is_uuid(self):
        import uuid
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        uuid.UUID(case.id)  # raises if not valid UUID

    def test_touch_updates_timestamp(self):
        import time
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        before = case.updatedAt
        time.sleep(0.01)
        case.touch()
        assert case.updatedAt > before

    def test_timestamps_are_utc(self):
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        assert case.createdAt.tzinfo is not None


class TestExtractedData:
    def test_confidence_bounds(self):
        from pydantic import ValidationError
        import pytest
        with pytest.raises(ValidationError):
            ExtractedData(confidence=1.5)
        with pytest.raises(ValidationError):
            ExtractedData(confidence=-0.1)

    def test_defaults(self):
        ed = ExtractedData()
        assert ed.vendor is None
        assert ed.line_items == []
        assert ed.warnings == []


class TestGoblinRegistry:
    def test_ledgergut_exists(self):
        assert "ledgergut" in GOBLIN_BY_ID

    def test_ledgergut_accepts_receipt_reimbursement(self):
        goblin = GOBLIN_BY_ID["ledgergut"]
        assert CaseType.RECEIPT_REIMBURSEMENT in goblin.acceptedCaseTypes

    def test_ledgergut_is_finance(self):
        goblin = GOBLIN_BY_ID["ledgergut"]
        assert goblin.division == GoblinDivision.FINANCE
