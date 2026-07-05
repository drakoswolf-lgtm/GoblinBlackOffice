from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.database import SessionLocal, init_db
from app.services.ledgergut_service import seed_sample_receipts


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_sample_receipts(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Goblin Black Office MVP Backend", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
