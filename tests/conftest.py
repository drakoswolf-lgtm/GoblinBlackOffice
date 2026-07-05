from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVER_PATH = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_PATH))

TEST_DB_PATH = Path(__file__).resolve().parents[1] / "test_gbo.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.database import SessionLocal, reset_db
from app.main import app
from app.services.ledgergut_service import seed_sample_receipts


@pytest.fixture(autouse=True)
def fresh_database():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    reset_db()
    with SessionLocal() as db:
        seed_sample_receipts(db)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
