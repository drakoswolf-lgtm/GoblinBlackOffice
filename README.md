# 🧌 Goblin Black Office

A personal workforce of disgruntled goblins dedicated to saving you time,
making you money, and leaving suspicious slime and coffee stains on your TPS reports.

---

## Quick Start

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

### Tests

```bash
cd backend
source .venv/bin/activate && pytest -q
```

---

## Structure

```
GoblinBlackOffice/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── models/
│   │   │   ├── case.py              # Case / Operation model
│   │   │   └── goblin.py            # Goblin / Operative model + registry
│   │   ├── services/
│   │   │   ├── workflow.py          # Stage transition engine
│   │   │   ├── ledgergut.py         # Receipt extraction (regex)
│   │   │   ├── generator.py         # Reimbursement package generator
│   │   │   └── store.py             # In-memory case store
│   │   └── routers/
│   │       ├── cases.py             # Case lifecycle endpoints
│   │       └── goblins.py           # Operative lookup endpoints
│   └── tests/
│       ├── test_models.py
│       ├── test_workflow.py
│       ├── test_ledgergut.py
│       └── test_api.py
├── frontend/
│   └── src/
│       ├── App.jsx                  # Root + routing
│       ├── api/client.js            # API wrapper
│       ├── pages/
│       │   ├── Dashboard.jsx        # Case list
│       │   ├── GoblinPick.jsx       # Operative selection
│       │   └── CaseFlow.jsx         # Per-case workflow shell
│       └── components/
│           ├── StageIntake.jsx      # Upload evidence
│           ├── StageReview.jsx      # Edit extracted data + approve
│           ├── StageComplete.jsx    # Download + archive
│           ├── ConfidenceMeter.jsx  # Confidence bar
│           └── StatusBadge.jsx      # Status pill
└── docs/
    └── REFERENCE_GOBLIN_WORKFLOW.md # Blueprint for future goblins
```

---

## Operatives

| Goblin | Division | Case Type | Status |
|---|---|---|---|
| **Ledgergut** | Finance | `receipt_reimbursement` | ✅ Active |

See [`docs/REFERENCE_GOBLIN_WORKFLOW.md`](docs/REFERENCE_GOBLIN_WORKFLOW.md)
for the full blueprint on adding new operatives.

---

## Workflow

```
intake → extraction → review → generation → completion → archived
```

1. **Intake** — Upload receipt (PDF, image, or text)
2. **Extraction** — Ledgergut reads the receipt and extracts vendor / date / total
3. **Review** — Verify and correct extracted data, tick the approval box
4. **Generation** — Ledgergut produces a reimbursement package
5. **Completion** — Download the package, archive the case
