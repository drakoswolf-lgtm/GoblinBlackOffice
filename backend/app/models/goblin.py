"""
Goblin / Operative model — the agent assigned to process cases.

Each goblin declares which CaseTypes it handles and what capabilities it
exposes.  Ledgergut is registered here as the reference operative.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel

from app.models.case import CaseType


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class GoblinDivision(str, Enum):
    FINANCE = "finance"
    LEGAL = "legal"
    OPERATIONS = "operations"
    RESEARCH = "research"


class GoblinStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


# ---------------------------------------------------------------------------
# Core Goblin model
# ---------------------------------------------------------------------------


class Goblin(BaseModel):
    id: str
    name: str
    division: GoblinDivision
    title: str
    status: GoblinStatus
    capabilities: List[str]
    acceptedCaseTypes: List[CaseType]
    flavor: str  # lore / personality blurb


# ---------------------------------------------------------------------------
# Goblin registry — add new operatives here
# ---------------------------------------------------------------------------

GOBLIN_REGISTRY: List[Goblin] = [
    Goblin(
        id="ledgergut",
        name="Ledgergut",
        division=GoblinDivision.FINANCE,
        title="Receipt Intelligence Officer",
        status=GoblinStatus.AVAILABLE,
        capabilities=[
            "receipt_parsing",
            "expense_validation",
            "reimbursement_package_generation",
        ],
        acceptedCaseTypes=[CaseType.RECEIPT_REIMBURSEMENT],
        flavor=(
            "Ledgergut is a squat, ink-stained goblin with an uncanny eye for "
            "suspicious totals and expired receipts.  He has processed over "
            "40,000 expense claims and once caught a VP expensing a dragon.  "
            "He considers that his finest hour."
        ),
    ),
]

GOBLIN_BY_ID: dict[str, Goblin] = {g.id: g for g in GOBLIN_REGISTRY}
