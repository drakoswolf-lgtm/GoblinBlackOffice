# Reference Goblin Workflow

> *"Ledgergut is not a feature. He is a precedent."*

## Overview

This document describes the canonical workflow pattern used by **Ledgergut**,
the Goblin Black Office's first operative. Every future goblin **must** follow
this pattern so that a single UI shell, a single API contract, and a single
test harness can cover the entire operative roster.

---

## 1. Core Models

### Case (Operation)

The `Case` model (`backend/app/models/case.py`) is the universal unit of work.
Every case, regardless of the assigned goblin, carries:

| Field | Purpose |
|---|---|
| `id` | UUID, auto-generated |
| `type` | `CaseType` enum — which goblin handles it |
| `assignedGoblinId` | Foreign key into the Goblin registry |
| `status` | Current workflow stage (see §3) |
| `createdAt` / `updatedAt` | Audit timestamps (UTC) |
| `evidenceFiles` | Paths to uploaded source documents |
| `extractedData` | Raw output from the goblin's extraction engine |
| `reviewedData` | Human-verified / corrected data |
| `outputFiles` | Generated deliverables |
| `confidence` | 0–1 float; mirrors `extractedData.confidence` |
| `warnings` | List of issues flagged during extraction |
| `statusMessage` | Human-readable description of current state |

**Adding a new case type:** add a value to `CaseType` in `case.py`.

### Goblin (Operative)

The `Goblin` model (`backend/app/models/goblin.py`) describes an operative:

| Field | Purpose |
|---|---|
| `id` | Slug (e.g. `ledgergut`) |
| `name` | Display name |
| `division` | Finance / Legal / Operations / Research |
| `title` | Flavourful job title |
| `status` | available / busy / offline |
| `capabilities` | List of capability tags (shown in UI) |
| `acceptedCaseTypes` | Which `CaseType` values this goblin handles |
| `flavor` | Lore blurb shown on the operative selection screen |

**Registering a new goblin:** append a `Goblin(...)` instance to
`GOBLIN_REGISTRY` in `goblin.py`.

---

## 2. Workflow Stages

Defined in `backend/app/services/workflow.py`.

```
intake → extraction → review → generation → completion → archived
                                                   ↕
                                                 failed
```

| Stage | Description |
|---|---|
| `intake` | Case created. Waiting for evidence upload. |
| `extraction` | Goblin is parsing the evidence. |
| `review` | Extraction complete. Human must verify data. |
| `generation` | Goblin is generating the output package. |
| `completion` | Package ready. Case can be downloaded and archived. |
| `archived` | Ledgergut has filed it away. Read-only. |
| `failed` | Something went wrong. Case can be corrected and re-extracted. |

**Transition rules** are enforced by `advance_case(case)` and `fail_case(case, reason)`.
No code should mutate `case.status` directly.

---

## 3. API Contract

All cases share the same REST surface (`/cases/*`). The workflow is driven by
**action endpoints**, not by passing a `status` field in a PUT body:

| Method | Path | Stage transition |
|---|---|---|
| `POST` | `/cases` | → `intake` |
| `POST` | `/cases/{id}/evidence` | (uploads files, stays in `intake`) |
| `POST` | `/cases/{id}/extract` | `intake` → `extraction` → `review` |
| `PUT` | `/cases/{id}/review` | stays in `review` (saves data) |
| `POST` | `/cases/{id}/generate` | `review` → `generation` → `completion` |
| `POST` | `/cases/{id}/archive` | `completion` → `archived` |
| `GET` | `/cases/{id}/download/{filename}` | download output file |

Goblin lookup: `GET /goblins`, `GET /goblins/{id}`.

---

## 4. Ledgergut Implementation (Reference)

**Case type:** `receipt_reimbursement`

**Extraction service:** `backend/app/services/ledgergut.py`

Ledgergut's `extract(file_path) → ExtractedData` function:

1. Reads the file by extension (`.pdf`, `.txt`, `.csv`, `.jpg`, `.png`, …).
2. For PDFs: extracts text using **pypdf**.
3. Applies regex heuristics to locate vendor name, date, and total amount.
4. Returns an `ExtractedData` payload with `confidence` (0–1) and `warnings`.

**Package generation:** `backend/app/services/generator.py`

`generate_reimbursement_package(case, output_dir) → str`

Writes a structured plain-text reimbursement document and returns its path.

---

## 5. UI Pattern

The frontend (`frontend/src/`) implements the same five stages as the API.

```
GoblinPick → CaseFlow
               ├── StageIntake     (upload evidence, submit)
               ├── [extraction]    (auto-polling spinner)
               ├── StageReview     (edit fields, approve, generate)
               ├── StageComplete   (download, archive)
               └── [failed]        (error message, retry intake)
```

Key components:

| Component | Responsibility |
|---|---|
| `pages/GoblinPick` | Select operative → create case |
| `pages/CaseFlow` | Outer shell: loads case, routes to stage component |
| `components/StageIntake` | File upload + extraction trigger |
| `components/StageReview` | Editable field form + approval checkbox |
| `components/StageComplete` | Download link + archive action |
| `components/ConfidenceMeter` | Visual bar: green/gold/red by confidence |
| `components/StatusBadge` | Coloured pill for case status |
| `api/client.js` | Thin fetch wrapper for all API calls |

---

## 6. Adding a New Goblin

Follow these steps to add `Inkshriek` (contract review) as a second operative:

### 6.1 Register the case type

```python
# backend/app/models/case.py
class CaseType(str, Enum):
    RECEIPT_REIMBURSEMENT = "receipt_reimbursement"
    CONTRACT_REVIEW       = "contract_review"   # ← add
```

### 6.2 Register the goblin

```python
# backend/app/models/goblin.py  (in GOBLIN_REGISTRY)
Goblin(
    id="inkshriek",
    name="Inkshriek",
    division=GoblinDivision.LEGAL,
    title="Senior Contract Analyst",
    status=GoblinStatus.AVAILABLE,
    capabilities=["clause_extraction", "risk_flagging", "redline_generation"],
    acceptedCaseTypes=[CaseType.CONTRACT_REVIEW],
    flavor="Inkshriek smells of old vellum and unresolved disputes.",
)
```

### 6.3 Write the extraction service

```python
# backend/app/services/inkshriek.py
from app.models.case import ExtractedData

def extract(file_path: str) -> ExtractedData:
    ...
```

### 6.4 Wire the router

In `backend/app/routers/cases.py`, the `run_extraction` endpoint already calls
`ledgergut_service.extract(...)` for `receipt_reimbursement`. Add a dispatch:

```python
from app.services import inkshriek as inkshriek_service

EXTRACTION_MAP = {
    CaseType.RECEIPT_REIMBURSEMENT: ledgergut_service.extract,
    CaseType.CONTRACT_REVIEW:       inkshriek_service.extract,
}

result = EXTRACTION_MAP[case.type](case.evidenceFiles[0])
```

### 6.5 Write the generator

Add `backend/app/services/inkshriek_generator.py` and update `generate_package`
similarly.

### 6.6 (Optional) Custom UI stage

If Inkshriek needs a different review form, create
`frontend/src/components/StageReviewContract.jsx` and add a conditional in
`CaseFlow.jsx`:

```jsx
{status === 'review' && caseData.type === 'contract_review' && (
  <StageReviewContract caseData={caseData} onUpdate={refresh} />
)}
```

The outer `CaseFlow` shell, progress bar, status messages, and confidence meter
all work automatically — you only swap the inner stage component.

---

## 7. Testing Conventions

- Unit tests for models: `backend/tests/test_models.py`
- Unit tests for workflow engine: `backend/tests/test_workflow.py`
- Unit tests for extraction: `backend/tests/test_ledgergut.py`
- Integration (API) tests: `backend/tests/test_api.py`

Run: `cd backend && source .venv/bin/activate && pytest -q`

Each new goblin should add a matching `test_<goblin>.py` for its extraction
service and extend `test_api.py` with its full lifecycle.

---

## 8. Design Principles

1. **Stage names are sacred.** `intake → extraction → review → generation → completion → archived` is the universal spine. Goblins may skip stages (e.g. no extraction needed) but must not rename them.

2. **The workflow engine is the only gatekeeper.** Call `advance_case()` and `fail_case()`. Never mutate `case.status` directly.

3. **Extraction is always separate from generation.** Humans must be able to review and correct data before any output is produced.

4. **Confidence is mandatory.** Every extraction must return a 0–1 confidence score. Zero means "I have no idea, please fill this in."

5. **Failure is a first-class state.** Every goblin's extraction and generation code must be wrapped in `try/except` that calls `fail_case()`. The UI must handle this gracefully.

6. **One API, many goblins.** The `/cases` endpoints do not change when a new goblin is added. Only the extraction and generation services are goblin-specific.
