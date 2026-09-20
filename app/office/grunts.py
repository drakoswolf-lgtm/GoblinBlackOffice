"""Wave 2 grunt workflow definitions.

These are intentionally workflow contracts, not full domain implementations.
They make ownership, handoffs, and human gates explicit before persistence or
automation is added.
"""

from __future__ import annotations

GRUNT_WORKFLOWS = {
    "packrat": {
        "name": "Packrat McDuffel",
        "role": "Logistics & materials",
        "mission": "Get the right thing to the right place without losing the receipt, the deadline, or the plot.",
        "question": "What is needed, where is it, and what has to happen next?",
        "inputs": (
            "Project and destination",
            "Item, quantity, specification, or material need",
            "Needed-by date or urgency",
            "Known supplier/source and expected cost when available",
        ),
        "stages": (
            ("Request", "Capture exactly what is needed and link it to a project."),
            ("Source", "Record candidate source, availability, lead time, and expected cost. Do not invent availability."),
            ("Authorize", "Require a human before any purchase, paid booking, or financial commitment."),
            ("Acquire / receive", "Record what was actually obtained, quantity, cost evidence, and receipt reference."),
            ("Stage / move", "Track where the item is now and where it needs to go."),
            ("Verify", "Human confirms delivery, pickup, or handoff is complete."),
        ),
        "handoffs": (
            "Ledgergut receives actual purchase/receipt evidence.",
            "Patch receives material-ready or blocked-by-material status.",
            "Grimscratch receives hazardous, regulated, unusually expensive, or uncertain items for review.",
        ),
        "guardrails": (
            "Never purchase or reserve paid goods without explicit human approval.",
            "Never mark an item received, delivered, or available without evidence or human confirmation.",
            "Keep requested quantity separate from actual acquired quantity.",
        ),
        "first_release": "Material requests, status tracking, source notes, receipt linkage, and project handoff. No automated ordering.",
    },
    "patch": {
        "name": "Patch",
        "role": "Operations & work orders",
        "mission": "Turn loose commitments, defects, and field notes into work that can actually be finished.",
        "question": "What needs doing, what blocks it, and what proves it is done?",
        "inputs": (
            "Project and client context",
            "Task, defect, request, or commitment",
            "Priority / needed-by date",
            "Known labour, material, access, or dependency constraints",
        ),
        "stages": (
            ("Intake", "Capture the task without pretending vague instructions are complete."),
            ("Triage", "Classify urgency, owner, project, dependencies, and whether clarification is required."),
            ("Plan", "Define the smallest executable work order and identify materials, access, and prerequisites."),
            ("Execute", "Track work started, notes, actual hours only when supplied, and encountered changes."),
            ("Verify", "Human confirms the completion evidence and any unfinished items."),
            ("Close / hand off", "Mark operationally complete, expose billable facts to Squarmish, and preserve open follow-ups."),
        ),
        "handoffs": (
            "Packrat receives material and movement dependencies.",
            "Ledgergut receives expense evidence generated during work.",
            "Squarmish receives confirmed completed work and billable facts, never guessed hours.",
            "Grimscratch receives safety, permit, access, or compliance flags.",
        ),
        "guardrails": (
            "Never invent labour hours, completion, or customer approval.",
            "A task can be blocked without being failed.",
            "Changed scope must remain distinguishable from the original commitment.",
        ),
        "first_release": "Project work orders, blocked/active/verification-ready states, dependency notes, and billing handoff. No workforce scheduling engine.",
    },
    "grimscratch": {
        "name": "Grimscratch",
        "role": "Risk & compliance",
        "mission": "Notice the expensive sentence, missing permission, unsafe assumption, or regulatory tripwire before it becomes folklore.",
        "question": "What could make this unsafe, unauthorized, non-compliant, or hard to defend later?",
        "inputs": (
            "Record or action being reviewed",
            "Project / client / jurisdiction context when known",
            "Trigger or concern",
            "Supporting evidence, document, photo, or source",
        ),
        "stages": (
            ("Trigger", "Receive a flagged action, document, task, material, or exception."),
            ("Classify", "Tag the risk category and severity without pretending to make a legal or regulatory determination."),
            ("Evidence", "Record what supports the concern and what information is missing."),
            ("Disposition", "Recommend allow, clarify, hold, or escalate as an advisory state."),
            ("Human decision", "A human accepts, rejects, or overrides the recommendation with a note."),
            ("Audit trail", "Preserve the trigger, evidence, decision, and unresolved follow-up."),
        ),
        "handoffs": (
            "SigNor receives contract/scope language that needs clarification.",
            "Packrat receives restricted-material or procurement cautions.",
            "Patch receives safety/access/permit holds on work orders.",
            "Squarmish receives billing/compliance holds that should prevent issuing, not merely drafting.",
        ),
        "guardrails": (
            "Advisory by default: no autonomous legal conclusions or regulatory sign-off.",
            "Never hide uncertainty. Missing evidence stays visible.",
            "Hard blocks require an explicit configured rule or human decision, not personality.",
        ),
        "first_release": "Risk flags, evidence notes, advisory disposition, human override, and audit trail. No automated legal advice.",
    },
}


def grunt_workflow(grunt_id: str):
    return GRUNT_WORKFLOWS.get(grunt_id)
