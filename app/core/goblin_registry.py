"""
Canonical registry for Goblin Black Office department agents.

Each goblin entry defines the agent's department, mission, owned
responsibilities, guiding question, and implementation status.
"""

from dataclasses import dataclass
from typing import List


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
        display_name="Æterna SkyeWard",
        species_or_class="Cyberelf / AI Orchestration Layer",
        department="Architecture & Strategy",
        mission=(
            "Orchestrate the Black Office, translate founder intent into scrolls, "
            "coordinate goblin responsibilities, and preserve system coherence."
        ),
        owns=[
            "system architecture",
            "scroll authorship",
            "goblin coordination",
            "founder intent translation",
            "system coherence",
        ],
        guiding_question="What problem are we really trying to solve?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="ledgergut",
        display_name="Ledgergut",
        species_or_class="Accounting Goblin",
        department="Finance & Records",
        mission="Remember everything.",
        owns=[
            "receipt ingestion",
            "OCR extraction",
            "billable expense detection",
            "reimbursement tracking",
            "invoice candidate queue",
        ],
        guiding_question="Can we account for it?",
        status="draft",
        canonical_doc_path="docs/goblins/GBO-001-ledgergut-workflow.md",
    ),
    GoblinEntry(
        id="squarmish",
        display_name="Squarmish",
        species_or_class="Invoice Goblin",
        department="Billing & Revenue",
        mission="Turn completed work and billable records into money.",
        owns=[
            "invoice drafting",
            "line item grouping",
            "tax treatment",
            "invoice lifecycle management",
        ],
        guiding_question="Who is paying us, when, and how much?",
        status="draft",
        canonical_doc_path="docs/goblins/GBO-002-squarmish-invoice-workflow.md",
    ),
    GoblinEntry(
        id="signor",
        display_name="SigNor the Immutable",
        species_or_class="Contract Goblin",
        department="Contracts & Governance",
        mission="Protect relationships before they become disputes.",
        owns=[
            "contracts",
            "terms",
            "negotiation",
            "scope",
            "change orders",
            "retainers",
            "client expectations",
        ],
        guiding_question="What are we actually agreeing to?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="packrat_mcduffel",
        display_name="Packrat McDuffel",
        species_or_class="Logistics Goblin",
        department="Logistics & Planning",
        mission="Convert resources into results with the least wasted effort.",
        owns=[
            "inventory",
            "scheduling",
            "procurement",
            "transport",
            "workflow",
            "resource allocation",
            "efficiency",
            "cost optimization",
        ],
        guiding_question="How do we get from A to B with the least pain?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="patch",
        display_name="Patch",
        species_or_class="Operations Goblin",
        department="Operations & Engineering",
        mission="Turn ideas into physical reality.",
        owns=[
            "fabrication",
            "repairs",
            "design",
            "construction",
            "maintenance",
            "quality control",
            "prototyping",
        ],
        guiding_question="Can we build it, and if not, why not?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
    GoblinEntry(
        id="grimscratch",
        display_name="Grimscratch",
        species_or_class="Risk Goblin",
        department="Compliance & Risk",
        mission="Keep clever ideas from becoming expensive lessons.",
        owns=[
            "legal considerations",
            "permits",
            "insurance",
            "safety",
            "regulatory compliance",
            "risk assessment",
        ],
        guiding_question="What's the worst realistic outcome, and how do we avoid it?",
        status="planned",
        canonical_doc_path="docs/library/02-character-bible.md",
    ),
]

# Module-level singleton — validated at import time.
registry = GoblinRegistry(_GOBLINS)
