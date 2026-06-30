# Setup Instructions

## Mobile (`mobile/`)

1. Install Flutter SDK.
2. From the `mobile/` directory run:
   - `flutter pub get`
   - `flutter run`

## Server (`server/`)

1. Create and activate a Python virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start API server:
   - `uvicorn app.main:app --reload --app-dir server`

## Tests (`tests/`)

Run repository scaffolding validation:

- `python -m unittest discover -s tests -p 'test_*.py'`
