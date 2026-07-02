"""
Goblin Black Office — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import cases, goblins

app = FastAPI(
    title="Goblin Black Office",
    description=(
        "A personal workforce of disgruntled goblins dedicated to saving you "
        "time, making you money, and leaving suspicious slime on your TPS reports."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(goblins.router)


@app.get("/")
def root() -> dict:
    return {
        "service": "Goblin Black Office",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
