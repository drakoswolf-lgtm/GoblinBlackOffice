"""
Thin in-memory case store.

Intentionally simple — swap for a real database without touching the routers.
"""

from __future__ import annotations

from typing import Dict, Optional

from app.models.case import Case

_store: Dict[str, Case] = {}


def save(case: Case) -> Case:
    _store[case.id] = case
    return case


def get(case_id: str) -> Optional[Case]:
    return _store.get(case_id)


def all_cases() -> list[Case]:
    return list(_store.values())


def delete(case_id: str) -> bool:
    if case_id in _store:
        del _store[case_id]
        return True
    return False
