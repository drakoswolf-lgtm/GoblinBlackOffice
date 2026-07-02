"""
Tests for the workflow engine.
"""

import pytest

from app.models.case import Case, CaseStatus, CaseType
from app.services.workflow import WorkflowError, advance_case, fail_case


class TestAdvanceCase:
    def _case(self):
        return Case(type=CaseType.RECEIPT_REIMBURSEMENT)

    def test_intake_to_extraction(self):
        case = self._case()
        assert case.status == CaseStatus.INTAKE
        advance_case(case)
        assert case.status == CaseStatus.EXTRACTION

    def test_full_happy_path(self):
        case = self._case()
        expected = [
            CaseStatus.EXTRACTION,
            CaseStatus.REVIEW,
            CaseStatus.GENERATION,
            CaseStatus.COMPLETION,
            CaseStatus.ARCHIVED,
        ]
        for stage in expected:
            advance_case(case)
            assert case.status == stage

    def test_cannot_advance_from_archived(self):
        case = self._case()
        for _ in range(5):
            advance_case(case)
        assert case.status == CaseStatus.ARCHIVED
        with pytest.raises(WorkflowError):
            advance_case(case)

    def test_cannot_advance_from_failed(self):
        case = self._case()
        fail_case(case, "test failure")
        with pytest.raises(WorkflowError):
            advance_case(case)

    def test_touch_is_called(self):
        import time
        case = self._case()
        before = case.updatedAt
        time.sleep(0.01)
        advance_case(case)
        assert case.updatedAt > before

    def test_status_message_is_updated(self):
        case = self._case()
        advance_case(case)
        assert "scrutinis" in case.statusMessage.lower() or case.statusMessage != ""


class TestFailCase:
    def test_fail_sets_status(self):
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        fail_case(case, "network error")
        assert case.status == CaseStatus.FAILED

    def test_fail_appends_warning(self):
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        fail_case(case, "my reason")
        assert "my reason" in case.warnings

    def test_fail_sets_message(self):
        case = Case(type=CaseType.RECEIPT_REIMBURSEMENT)
        fail_case(case, "bad file")
        assert "bad file" in case.statusMessage
