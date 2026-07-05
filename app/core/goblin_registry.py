"""
Canonical registry for Goblin Black Office department agents.

Each goblin entry defines the agent's department, mission, owned
responsibilities, guiding question, and implementation status.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class GoblinEntry:
    id: str
    display_name: str
    species_or_class: str
    department: str
    mission: str
    owns: List[str]
    guiding_question: str
    status: str
    canonical_doc_path: str


class GoblinRegistry:
    """
    In-memory registry of all Goblin Black Office agents.

    Enforces unique ids and requires each goblin to own at least one
    responsibility.  Exposes ``get_all()`` and ``get_by_id()`` for
    read-only access.
    """

    def __init__(self, entries: List[GoblinEntry]) -> None:
        seen: dict = {}
        for entry in entries:
            if not entry.owns:
                raise ValueError(
                    f"Goblin '{entry.id}' must own at least one responsibility."
                )
            if entry.id in seen:
                raise ValueError(f"Duplicate goblin id: '{entry.id}'")
            seen[entry.id] = entry
        self._registry: dict = seen

    def get_all(self) -> List[GoblinEntry]:
        """Return all registered goblins."""
        return list(self._registry.values())

    def get_by_id(self, goblin_id: str) -> GoblinEntry:
        """
        Return the goblin with the given id.

        Raises ``KeyError`` if no goblin with that id exists.
        """
        if goblin_id not in self._registry:
            raise KeyError(f"No goblin found with id: '{goblin_id}'")
        return self._registry[goblin_id]


# ---------------------------------------------------------------------------
# Canonical goblin definitions
# ---------------------------------------------------------------------------

_GOBLINS: List[GoblinEntry] = [
    GoblinEntry(
        id="aeterna_skyeward",
        display_name="Aeterna Skyeward",
        species_or_class="Sky Goblin",
        department="Scheduling & Planning",
        mission=(
            "Tracks job timelines, coordinates deadlines, and ensures the right "
            "work lands in the right hands at the right moment."
        ),
        owns=[
            "job scheduling",
            "deadline tracking",
            "calendar coordination",
            "handoff timing",
        ],
        guiding_question="What needs to happen next, and when does it need to happen?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="ledgergut",
        display_name="Ledgergut",
        species_or_class="Accounting Goblin",
        department="Finance & Accounting",
        mission=(
            "Ingests submitted receipts, extracts financial data via OCR, assigns "
            "operational context, and routes records to review or invoice queues."
        ),
        owns=[
            "receipt ingestion",
            "OCR extraction",
            "billable expense detection",
            "reimbursement tracking",
            "invoice candidate queue",
        ],
        guiding_question="Who paid for this, and does anyone owe money for it?",
        status="draft",
        canonical_doc_path="docs/goblins/GBO-001-ledgergut-workflow.md",
    ),
    GoblinEntry(
        id="squarmish",
        display_name="Squarmish",
        species_or_class="Invoice Goblin",
        department="Finance & Invoicing",
        mission=(
            "Turns billable receipt records from Ledgergut's candidate queue into "
            "draft invoices grouped by client and project, ready for human review."
        ),
        owns=[
            "invoice drafting",
            "line item grouping",
            "tax treatment",
            "invoice lifecycle management",
        ],
        guiding_question="What has been billed, and what still needs to go out the door?",
        status="draft",
        canonical_doc_path="docs/goblins/GBO-002-squarmish-invoice-workflow.md",
    ),
    GoblinEntry(
        id="signor",
        display_name="Signor",
        species_or_class="Contract Goblin",
        department="Document Management",
        mission=(
            "Manages client contracts, service agreements, and document templates; "
            "tracks signature status and ensures nothing goes unsigned or misfiled."
        ),
        owns=[
            "contract tracking",
            "document templates",
            "signature status monitoring",
            "client agreement records",
        ],
        guiding_question="Is everything signed, sealed, and filed where we can find it?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="packrat_mcduffel",
        display_name="Packrat McDuffel",
        species_or_class="Archive Goblin",
        department="Records & Storage",
        mission=(
            "Archives approved records, receipts, and documents; maintains a "
            "retrievable, auditable trail of everything that passes through the office."
        ),
        owns=[
            "record archival",
            "file retrieval",
            "audit trail maintenance",
            "document versioning",
        ],
        guiding_question="Where did we put that, and can we find it again if anyone asks?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="patch",
        display_name="Patch",
        species_or_class="Operations Goblin",
        department="Operations",
        mission=(
            "Monitors ongoing jobs and tasks, flags unresolved work-in-progress items, "
            "and ensures nothing quietly falls off the plate."
        ),
        owns=[
            "job status tracking",
            "work-in-progress resolution",
            "maintenance scheduling",
            "operational alerts",
        ],
        guiding_question="What is still broken, and who is supposed to be fixing it?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="grimscratch",
        display_name="Grimscratch",
        species_or_class="Audit Goblin",
        department="Audit & Compliance",
        mission=(
            "Reviews flagged records, catches anomalies, enforces data quality checks "
            "across all goblin outputs, and ensures every number survives scrutiny."
        ),
        owns=[
            "record review queue",
            "anomaly detection",
            "data quality checks",
            "cross-goblin audit",
        ],
        guiding_question=(
            "Does this actually add up, and will it hold up if someone looks closely?"
        ),
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
]

# Module-level singleton — validated at import time.
registry = GoblinRegistry(_GOBLINS)
