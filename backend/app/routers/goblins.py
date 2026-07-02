"""Goblins router — list operatives and their capabilities."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.goblin import Goblin, GOBLIN_REGISTRY, GOBLIN_BY_ID

router = APIRouter(prefix="/goblins", tags=["goblins"])


@router.get("", response_model=List[Goblin])
def list_goblins() -> List[Goblin]:
    return GOBLIN_REGISTRY


@router.get("/{goblin_id}", response_model=Goblin)
def get_goblin(goblin_id: str) -> Goblin:
    goblin = GOBLIN_BY_ID.get(goblin_id)
    if goblin is None:
        raise HTTPException(status_code=404, detail=f"Goblin '{goblin_id}' not found.")
    return goblin
