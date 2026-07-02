"""
Workflow engine — enforces the canonical stage transitions shared by all goblins.

Stage order:
  intake → extraction → review → generation → completion → archived

Any stage may transition to `failed`.

Future goblins call `advance_case()` and `fail_case()` instead of mutating
status directly, so all state changes flow through one audited path.
"""

from __future__ import annotations

from app.models.case import Case, CaseStatus

# Legal forward transitions for the happy path
_TRANSITIONS: dict[CaseStatus, CaseStatus] = {
    CaseStatus.INTAKE: CaseStatus.EXTRACTION,
    CaseStatus.EXTRACTION: CaseStatus.REVIEW,
    CaseStatus.REVIEW: CaseStatus.GENERATION,
    CaseStatus.GENERATION: CaseStatus.COMPLETION,
    CaseStatus.COMPLETION: CaseStatus.ARCHIVED,
}

# Human-readable status messages keyed by destination status
_STATUS_MESSAGES: dict[CaseStatus, str] = {
    CaseStatus.INTAKE: "Awaiting evidence submission.",
    CaseStatus.EXTRACTION: "Goblin is scrutinising your receipt…",
    CaseStatus.REVIEW: "Extraction complete. Please verify the details below.",
    CaseStatus.GENERATION: "Generating reimbursement package…",
    CaseStatus.COMPLETION: "Package ready. Assignment complete.",
    CaseStatus.ARCHIVED: "Case archived. Ledgergut has filed it away.",
    CaseStatus.FAILED: "Something went wrong. Check warnings for details.",
}


class WorkflowError(Exception):
    """Raised when a requested stage transition is not permitted."""


def advance_case(case: Case) -> Case:
    """Advance *case* to the next canonical stage.

    Raises ``WorkflowError`` if the case is already at the terminal stage or
    is in a ``failed`` state.
    """
    next_status = _TRANSITIONS.get(case.status)
    if next_status is None:
        raise WorkflowError(
            f"Case {case.id} cannot advance from status '{case.status}'. "
            "It is either at a terminal stage or has failed."
        )
    case.status = next_status
    case.statusMessage = _STATUS_MESSAGES[next_status]
    case.touch()
    return case


def fail_case(case: Case, reason: str) -> Case:
    """Move *case* to the ``failed`` state with a descriptive reason."""
    case.status = CaseStatus.FAILED
    case.statusMessage = f"Failed: {reason}"
    case.warnings.append(reason)
    case.touch()
    return case


def status_message(status: CaseStatus) -> str:
    return _STATUS_MESSAGES.get(status, "Unknown status.")
