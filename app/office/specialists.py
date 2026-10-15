"""Presentation canon shared by the desk and project specialist channels.

Display identities follow the supplied 2026-10-14 panes. Legacy domain keys
(including grimscratch) remain unchanged; this catalogue does not grant abilities.
"""
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class Specialist:
    key: str
    name: str
    rank: str
    label: str
    role: str
    href: str
    note: str
    implemented: bool = True


SPECIALISTS = (
    Specialist("ledgergut", "Ledgergut", "LTJG", "Receipt Log", "Receipts & expenses", "/ledgergut/", "Capture, review and reconcile expenses."),
    Specialist("signor", "SigNor", "L.CDR", "Agreements", "Scope & terms", "/signor/", "Draft terms and keep scope defined."),
    Specialist("squarmish", "Squarmish", "CPO", "Invoices & Payments", "Billing & receivables", "/squarmish/", "Draft invoices and track receivables."),
    Specialist("packrat", "Packrat", "ENS", "Materials", "Shopping & requirements", "/workflows/packrat", "Plan requirements and reconcile supplies.", False),
    Specialist("patch", "Patch", "2PO", "Work Log", "Operations & labour", "/workflows/patch", "Record completed work and field time.", False),
    Specialist("grimsnatch", "Grimsnatch", "LT", "Risk Review", "Record-based checks", "/workflows/grimscratch", "Review risks and unresolved checks.", False),
)


@dataclass(frozen=True)
class SpecialistPanel:
    specialist: Specialist
    href: str
    summary: str
    state: str
    action: str


def desk_panels():
    return tuple(
        SpecialistPanel(
            specialist, specialist.href, specialist.note,
            "Workspace" if specialist.implemented else "Workflow guide",
            "Open workspace" if specialist.implemented else "Read workflow",
        )
        for specialist in SPECIALISTS
    )


def project_panels(project_id, *, expenses, agreements, invoices, shopping_items, work_logs):
    query = urlencode({"project_id": project_id})
    records = {
        "ledgergut": (f"/ledgergut/?{query}", expenses, "expense record", "expense records"),
        "signor": (f"/signor/?{query}", agreements, "agreement", "agreements"),
        "squarmish": ("#project-invoices", invoices, "invoice", "invoices"),
        "packrat": ("#packrat-shopping", shopping_items, "list item", "list items"),
        "patch": ("#project-work", work_logs, "work entry", "work entries"),
    }
    panels = []
    for specialist in SPECIALISTS:
        if specialist.key == "grimsnatch":
            panels.append(SpecialistPanel(
                specialist, f"/aeterna/command?{query}&view=checks",
                "Review checks from this project's records.", "Advisory", "Review checks",
            ))
        else:
            href, items, singular, plural = records[specialist.key]
            summary = f"{len(items)} {singular if len(items) == 1 else plural}"
            panels.append(SpecialistPanel(
                specialist, href, summary, "Project records", "Open records",
            ))
    return tuple(panels)
