# Goblin Black Office Architecture Overview

## High-level structure

- `mobile/`: Flutter mobile client scaffold (Material 3, dark-first with green accent, Android-first setup)
- `server/`: FastAPI REST API scaffold with modular services for OCR, reimbursement, and orchestration
- `shared/`: shared DTO schemas and constants for cross-platform contracts
- `templates/`: reimbursement Excel template storage
- `tests/`: repository-level test placeholders organized by area

## Service modularity

Each goblin should be an independent module/service with one responsibility.

- `ledgergut` (Receipt Goblin) is the first planned module
- OCR, reimbursement generation, and orchestration are separated as placeholders

## Current scope

This scaffold intentionally excludes business logic.
