# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut — Receipt Entry UI

### Quick start (fresh checkout)

```bash
# 1. Install Python dependencies (Python 3.10+ required)
pip install flask pillow pytesseract

# 2. Launch Ledgergut
PYTHONPATH=. python run_ledgergut.py
```

Then open **http://localhost:5000** in your browser.

The Ledgergut page lets you upload a receipt image, enter receipt details, run
validation, and save receipts to a local JSON file (`runtime/ledgergut/receipts.json`).
Saved receipts can be exported as CSV from the same page.

Uploaded images are stored in `runtime/ledgergut/images/` (gitignored).

### Local OCR dependency

Ledgergut receipt scanning uses **Tesseract OCR** locally through `pytesseract`.
Scanned values are only suggestions — always review and correct them before saving.

#### Install Tesseract

**Windows (Chocolatey)**

```powershell
choco install tesseract
```

**macOS (Homebrew)**

```bash
brew install tesseract
```

**Ubuntu**

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

If Tesseract is missing or unavailable, Ledgergut still supports full manual entry.

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
