# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut — Receipt Entry UI

### Quick start (fresh checkout)

```bash
# 1. Install dependencies (Python 3.10+ required)
pip install flask

# 2. Launch the web UI
python run_ledgergut.py
```

Then open **http://localhost:5000** in your browser.

The Ledgergut page lets you upload a receipt image, enter receipt details, run
validation, and save receipts to a local JSON file (`runtime/ledgergut/receipts.json`).
Saved receipts can be exported as CSV from the same page.

Uploaded images are stored in `runtime/ledgergut/images/` (gitignored).

### Running tests

```bash
# From the repository root
PYTHONPATH=. python -m pytest tests/
```

Requires `pytest>=7.0` (`pip install pytest`).

---

## Goblin Workflows

- [GBO-001: Ledgergut Founder/Operator Receipt Intelligence Workflow](docs/goblins/GBO-001-ledgergut-workflow.md)
- [GBO-002: Squarmish Invoice Workflow](docs/goblins/GBO-002-squarmish-invoice-workflow.md)

## Library

- [Scroll 001 — Living Codex](docs/library/01-living-codex.md) — Master index of agents, scrolls, and documents
- [Scroll 002 — Character Bible](docs/library/02-character-bible.md) — Canonical character and role definitions for all goblins
