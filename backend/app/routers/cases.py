"""Cases router — the backbone of the Goblin Black Office workflow API.

Endpoints implement the canonical stages:

  POST   /cases                    — create a case (intake)
  GET    /cases                    — list all cases
  GET    /cases/{id}               — get case detail
  POST   /cases/{id}/evidence      — upload evidence file(s)
  POST   /cases/{id}/extract       — run extraction (moves to review)
  PUT    /cases/{id}/review        — save user-reviewed data (stays in review)
  POST   /cases/{id}/generate      — generate output package
  POST   /cases/{id}/complete      — mark complete
  POST   /cases/{id}/archive       — archive
  DELETE /cases/{id}               — delete (dev/test only)
"""

from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from fastapi.responses import FileResponse

from app.models.case import Case, CaseCreate, CaseReviewUpdate, CaseStatus, CaseType
from app.models.goblin import GOBLIN_BY_ID
from app.services import store
from app.services.workflow import WorkflowError, advance_case, fail_case
from app.services import ledgergut as ledgergut_service
from app.services.generator import generate_reimbursement_package

router = APIRouter(prefix="/cases", tags=["cases"])

# Directory where uploaded evidence and generated output are stored.
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "data/evidence")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data/output")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_404(case_id: str) -> Case:
    case = store.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case


def _require_status(case: Case, *statuses: CaseStatus) -> None:
    if case.status not in statuses:
        allowed = ", ".join(s.value for s in statuses)
        raise HTTPException(
            status_code=409,
            detail=(
                f"Case is in '{case.status}' status; "
                f"this action requires: {allowed}."
            ),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=Case, status_code=201)
def create_case(payload: CaseCreate) -> Case:
    """Create a new case and assign it to the appropriate goblin."""
    goblin_id = payload.assignedGoblinId

    # Auto-assign if not specified
    if goblin_id is None:
        if payload.type == CaseType.RECEIPT_REIMBURSEMENT:
            goblin_id = "ledgergut"

    if goblin_id and goblin_id not in GOBLIN_BY_ID:
        raise HTTPException(status_code=400, detail=f"Unknown goblin '{goblin_id}'.")

    goblin = GOBLIN_BY_ID.get(goblin_id) if goblin_id else None
    if goblin and payload.type not in goblin.acceptedCaseTypes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Goblin '{goblin_id}' does not accept case type '{payload.type}'."
            ),
        )

    case = Case(type=payload.type, assignedGoblinId=goblin_id)
    return store.save(case)


@router.get("", response_model=List[Case])
def list_cases() -> List[Case]:
    return store.all_cases()


@router.get("/{case_id}", response_model=Case)
def get_case(case_id: str) -> Case:
    return _get_or_404(case_id)


@router.post("/{case_id}/evidence", response_model=Case)
async def upload_evidence(
    case_id: str, files: List[UploadFile] = File(...)
) -> Case:
    """Upload one or more evidence files (receipts, PDFs, images)."""
    case = _get_or_404(case_id)
    _require_status(case, CaseStatus.INTAKE, CaseStatus.REVIEW)

    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    for upload in files:
        safe_name = f"{case_id}_{upload.filename}"
        dest = os.path.join(EVIDENCE_DIR, safe_name)
        content = await upload.read()
        with open(dest, "wb") as fh:
            fh.write(content)
        if dest not in case.evidenceFiles:
            case.evidenceFiles.append(dest)

    case.touch()
    return store.save(case)


@router.post("/{case_id}/extract", response_model=Case)
def run_extraction(case_id: str) -> Case:
    """Run Ledgergut's extraction engine on the uploaded evidence."""
    case = _get_or_404(case_id)
    _require_status(case, CaseStatus.INTAKE)

    if not case.evidenceFiles:
        raise HTTPException(
            status_code=400,
            detail="No evidence files uploaded. Please upload a receipt first.",
        )

    # Advance to EXTRACTION stage
    advance_case(case)

    try:
        # Use the first evidence file for extraction
        result = ledgergut_service.extract(case.evidenceFiles[0])
        case.extractedData = result
        case.confidence = result.confidence
        case.warnings = list(result.warnings)
    except Exception as exc:
        fail_case(case, str(exc))
        return store.save(case)

    # Advance to REVIEW stage
    advance_case(case)
    return store.save(case)


@router.put("/{case_id}/review", response_model=Case)
def save_review(case_id: str, payload: CaseReviewUpdate) -> Case:
    """Save user-reviewed / corrected data.  Keeps case in REVIEW status."""
    case = _get_or_404(case_id)
    _require_status(case, CaseStatus.REVIEW)

    from app.models.case import ReviewedData

    case.reviewedData = ReviewedData(**payload.model_dump())
    case.touch()
    return store.save(case)


@router.post("/{case_id}/generate", response_model=Case)
def generate_package(case_id: str) -> Case:
    """Generate the reimbursement output package."""
    case = _get_or_404(case_id)
    _require_status(case, CaseStatus.REVIEW)

    if case.reviewedData is None or not case.reviewedData.approved:
        raise HTTPException(
            status_code=400,
            detail="Case must be approved in the review step before generating.",
        )

    # Advance to GENERATION stage
    advance_case(case)

    try:
        output_path = generate_reimbursement_package(case, OUTPUT_DIR)
        case.outputFiles = [output_path]
    except Exception as exc:
        fail_case(case, f"Package generation failed: {exc}")
        return store.save(case)

    # Advance to COMPLETION
    advance_case(case)
    return store.save(case)


@router.post("/{case_id}/complete", response_model=Case)
def complete_case(case_id: str) -> Case:
    """Explicitly mark a case complete (idempotent if already complete)."""
    case = _get_or_404(case_id)
    if case.status == CaseStatus.COMPLETION:
        return case
    _require_status(case, CaseStatus.COMPLETION)
    return case


@router.post("/{case_id}/archive", response_model=Case)
def archive_case(case_id: str) -> Case:
    """Archive a completed case."""
    case = _get_or_404(case_id)
    _require_status(case, CaseStatus.COMPLETION)
    advance_case(case)
    return store.save(case)


@router.get("/{case_id}/download/{filename}")
def download_output(case_id: str, filename: str) -> FileResponse:
    """Download a generated output file."""
    case = _get_or_404(case_id)
    for fpath in case.outputFiles:
        if os.path.basename(fpath) == filename:
            if os.path.exists(fpath):
                return FileResponse(fpath, filename=filename)
    raise HTTPException(status_code=404, detail="File not found.")


@router.delete("/{case_id}")
def delete_case(case_id: str) -> Response:
    """Delete a case (development/testing only)."""
    _get_or_404(case_id)
    store.delete(case_id)
    return Response(status_code=204)
