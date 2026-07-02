# GoblinBlackOffice
A personal workforce of disgruntled goblins dedicated to saving you time, making you money, and leaving suspicious slime and coffee stains on your TPS reports.

## Ledgergut MVP Vertical Slice

### Backend (FastAPI)
- Path: `/home/runner/work/GoblinBlackOffice/GoblinBlackOffice/backend`
- Endpoints:
  - `GET /health`
  - `POST /ledgergut/extract`
  - `POST /ledgergut/generate-reimbursement`

Run:
```bash
cd /home/runner/work/GoblinBlackOffice/GoblinBlackOffice/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tests:
```bash
cd /home/runner/work/GoblinBlackOffice/GoblinBlackOffice/backend
source .venv/bin/activate
pytest -q
```

### Mobile Flutter UI
- Path: `/home/runner/work/GoblinBlackOffice/GoblinBlackOffice/mobile_app`
- Screens:
  - Home screen with Ledgergut card
  - Capture/upload screen
  - Review/edit screen
  - Success/export screen

Run (with Flutter SDK installed):
```bash
cd /home/runner/work/GoblinBlackOffice/GoblinBlackOffice/mobile_app
flutter pub get
flutter run
```
