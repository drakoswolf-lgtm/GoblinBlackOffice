# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Goblin Workflows

- [GBO-001: Ledgergut Founder/Operator Receipt Intelligence Workflow](docs/goblins/GBO-001-ledgergut-workflow.md)
- [GBO-002: Squarmish Invoice Workflow](docs/goblins/GBO-002-squarmish-invoice-workflow.md)

## Backend MVP Setup

1. Create a virtual environment:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
2. Install requirements:
   - `pip install -r server/requirements.txt`
3. Run the API:
   - `uvicorn app.main:app --reload --app-dir server`
4. Open Swagger docs:
   - `http://127.0.0.1:8000/docs`
5. Run tests:
   - `pytest`
