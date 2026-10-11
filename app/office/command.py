"""Æterna's read-only command intelligence, derived from Office-owned records.

No generated financial figures, autonomous state changes or inferred task completion.
Every lookup is business-scoped. Suggested priorities are advisory, not saved tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.ledger import LedgerSummary, summarize_business_ledger, summarize_project_ledger
from app.core.models import InvoiceStatus, RecordStatus


@dataclass(frozen=True)
class CommandAction:
    priority: int
    category: str
    title: str
    detail: str
    project_name: str
    href: str


@dataclass(frozen=True)
class GoblinCheck:
    name: str
    state: str
    summary: str
    href: str


@dataclass(frozen=True)
class ProjectBrief:
    project: object
    ledger: LedgerSummary
    actual_hours: Decimal
    estimate_total: Decimal | None
    agreement_count: int
    expense_count: int
    invoice_count: int
    receipt_evidence_count: int
    material_remaining: int
    actions: tuple[CommandAction, ...]
    checks: tuple[GoblinCheck, ...]


@dataclass(frozen=True)
class CommandBriefing:
    business_name: str
    currency: str
    project: object | None
    projects: tuple[object, ...]
    project_brief: ProjectBrief | None
    portfolio_checks: tuple[GoblinCheck, ...]
    ledger: LedgerSummary
    actual_hours: Decimal
    project_count: int
    active_count: int
    completed_count: int
    archived_count: int
    actions: tuple[CommandAction, ...]
    view: str
    question: str
    interpretation: str


VIEWS = ("overview", "totals", "priorities", "checks")
_PAID_STATES = {
    InvoiceStatus.APPROVED, InvoiceStatus.SENT, InvoiceStatus.DUE,
    InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID, InvoiceStatus.OVERDUE,
}


def resolve_view(view: str, question: str) -> tuple[str, str]:
    """A small, explicit intent router; this is not open-ended AI conversation."""
    q = (question or "").strip()[:180]
    if not q:
        return (view if view in VIEWS else "overview"), ""
    lowered = q.casefold()
    if any(word in lowered for word in ("money", "total", "balance", "outstanding", "owing", "unpaid", "invoice", "payment", "expense", "spent", "cost", "hour", "revenue", "paid")):
        return "totals", "FINANCIAL RECORDS"
    if any(word in lowered for word in ("priority", "priorities", "next", "urgent", "block", "action", "todo", "to do")):
        return "priorities", "ACTION QUEUE"
    if any(word in lowered for word in ("goblin", "specialist", "check", "ledgergut", "signor", "squarmish", "packrat", "patch", "grimscratch")):
        return "checks", "SPECIALIST STATUS"
    if any(word in lowered for word in ("overview", "brief", "status", "project", "report")):
        return "overview", "OFFICE OVERVIEW"
    return "overview", "LIMITED COMMANDS: TRY TOTALS, PRIORITIES OR GOBLIN CHECKS"


def _project_brief(store, business_id, project, currency, records):
    pid = project.project_id
    agreements = [r for r in records["agreements"] if r.project_id == pid]
    estimates = [r for r in records["estimates"] if r.project_id == pid]
    material_plans = [r for r in records["material_plans"] if r.project_id == pid]
    approved_ids = {p.material_plan_id for p in material_plans if p.approved}
    shopping = [r for r in records["shopping_items"] if r.project_id == pid and r.material_plan_id in approved_ids]
    expenses = [r for r in records["expenses"] if r.project_id == pid]
    work_logs = [r for r in records["work_logs"] if r.project_id == pid]
    invoices = [r for r in records["invoices"] if r.project_id == pid]
    ledger = summarize_project_ledger(
        business_id=business_id, project_id=pid, currency=currency,
        invoices=tuple(invoices), payments=tuple(records["payments"]), expenses=tuple(expenses),
    )
    hours = sum((r.hours for r in work_logs), Decimal("0"))
    remaining = [r for r in shopping if r.quantity_remaining > 0]
    actions = []
    href = f"/jobs/{pid}"

    def add(rank, category, title, detail, link):
        actions.append(CommandAction(rank, category, title, detail, project.name, link))

    if project.status == RecordStatus.ACTIVE:
        if not agreements:
            add(10, "SIG NOR", "Define the job agreement", "No agreement is recorded for this project.", f"/signor/?project_id={pid}")
        elif any(r.status.value == "draft" for r in agreements):
            add(20, "SIG NOR", "Review the agreement draft", "At least one agreement remains in draft.", href)
        if agreements and not estimates:
            add(30, "PLANNING", "Create a job estimate", "No project estimate is recorded. Hourly rates need no guessed total hours.", href)
        if remaining:
            add(40, "PACKRAT", "Check outstanding materials",
                f"{len(remaining)} shopping item(s) still show a remaining quantity.", href + "#packrat-shopping")

    drafts = [i for i in invoices if i.status == InvoiceStatus.DRAFT]
    if drafts:
        add(25, "SQUARMISH", "Review draft invoices", f"{len(drafts)} draft invoice(s) await human approval.", href)
    elif project.status == RecordStatus.COMPLETED and not invoices and (work_logs or expenses):
        add(35, "SQUARMISH", "Review final billing", "Field work is complete and costs or hours are recorded, but there is no invoice.", href)
    if ledger.outstanding > 0:
        add(45, "SQUARMISH", "Review outstanding balance", f"{currency} {ledger.outstanding:.2f} on issued/approved invoices remains unpaid.", href)
    if project.status == RecordStatus.COMPLETED and not drafts and ledger.outstanding == 0:
        add(80, "OFFICE", "Consider archiving completed work", "Field completion is recorded. Check final bills and follow-ups before archiving.", href)

    checks = (
        GoblinCheck("SigNor", "NO AGREEMENT" if not agreements else
            ("DRAFT EXISTS" if any(r.status.value == "draft" for r in agreements) else "RECORDED"),
            f"{len(agreements)} agreement record(s); this is not client acceptance.",
            f"/signor/?project_id={pid}"),
        GoblinCheck("Ledgergut", "RECORDED" if expenses else "NO PROJECT EXPENSES",
            f"{len(expenses)} project expense record(s). This does not prove all receipts were captured.",
            f"/ledgergut/?project_id={pid}"),
        GoblinCheck("Packrat", "MATERIALS REMAIN" if remaining else ("PLAN RECORDED" if material_plans else "NO PLAN"),
            f"{len(shopping)} approved shopping item(s); {len(remaining)} with remaining quantities.", href + "#packrat-shopping"),
        GoblinCheck("Patch", "FIELD COMPLETE" if project.status != RecordStatus.ACTIVE else
            ("LABOUR RECORDED" if work_logs else "NO LABOUR LOGS"),
            f"{len(work_logs)} work log(s); {hours} hours entered by users.", href),
        GoblinCheck("Squarmish", "DRAFTS FOR REVIEW" if drafts else ("BALANCE REMAINS" if ledger.outstanding > 0 else "RECORDED" if invoices else "NO INVOICES"),
            f"{len(invoices)} invoice record(s), {len(drafts)} draft(s); {currency} {ledger.outstanding:.2f} outstanding.", href),
        GoblinCheck("Grimscratch", "NOT AUTOMATED",
            "Risk and compliance checks are not yet implemented. No clearance is implied.", "/workflows/grimscratch"),
    )
    return ProjectBrief(
        project=project, ledger=ledger, actual_hours=hours,
        estimate_total=estimates[-1].total_estimate if estimates else None,
        agreement_count=len(agreements), expense_count=len(expenses),
        invoice_count=len(invoices),
        receipt_evidence_count=sum(bool(r.source_record_id) for r in expenses),
        material_remaining=len(remaining),
        actions=tuple(sorted(actions, key=lambda a: (a.priority, a.category, a.title))),
        checks=checks,
    )


def build_command_briefing(store, business_id: str, *, project_id: str = "", view: str = "overview", question: str = "") -> CommandBriefing:
    """Business-scoped live portfolio or project briefing. Raises LookupError for foreign IDs."""
    business = store.businesses.get(business_id, business_id)
    if business is None:
        raise LookupError("Business not found")
    all_projects = tuple(store.projects.list_for_business(business_id))
    selected = next((p for p in all_projects if p.project_id == project_id), None) if project_id else None
    if project_id and selected is None:
        raise LookupError("Project not found")
    records = {
        name: getattr(store, name).list_for_business(business_id)
        for name in ("agreements", "estimates", "material_plans", "shopping_items",
                     "expenses", "work_logs", "invoices", "payments")
    }
    currency = business.reporting_currency.upper()
    all_invoices = tuple(records["invoices"])
    all_expenses = tuple(records["expenses"])
    all_payments = tuple(records["payments"])
    project_briefs = [
        _project_brief(store, business_id, project, currency, records)
        for project in all_projects
    ]
    selected_brief = next((b for b in project_briefs if selected and b.project.project_id == selected.project_id), None)
    ledger = selected_brief.ledger if selected_brief else summarize_business_ledger(
        business_id=business_id, currency=currency,
        invoices=all_invoices, payments=all_payments, expenses=all_expenses,
    )
    hours = selected_brief.actual_hours if selected_brief else sum(
        (r.hours for r in records["work_logs"]), Decimal("0")
    )
    if selected_brief:
        actions = selected_brief.actions
    else:
        actions = tuple(sorted(
            (action for brief in project_briefs for action in brief.actions),
            key=lambda a: (a.priority, a.project_name.casefold(), a.title)
        ))
    draft_count = sum(i.status == InvoiceStatus.DRAFT for i in all_invoices)
    unresolved_materials = sum(
        1 for brief in project_briefs if brief.material_remaining > 0
    )
    remaining_lines = sum(brief.material_remaining for brief in project_briefs)
    total_agreements = len(records["agreements"])
    total_shopping = len(records["shopping_items"])
    total_labor_logs = len(records["work_logs"])
    portfolio_checks = (
        GoblinCheck("SigNor", "DRAFTS FOR REVIEW" if any(a.status.value == "draft" for a in records["agreements"]) else
            ("AGREEMENTS RECORDED" if total_agreements else "NO AGREEMENTS"),
            f"{total_agreements} agreement record(s) across this business. Client acceptance is a separate action.", "/signor/"),
        GoblinCheck("Ledgergut", "EXPENSES RECORDED" if all_expenses else "NO EXPENSES",
            f"{len(all_expenses)} expense record(s). Completeness of receipts is not verified.", "/ledgergut/"),
        GoblinCheck("Packrat", "MATERIALS REMAIN" if remaining_lines else
            ("MATERIALS RECORDED" if total_shopping else "NO MATERIAL LIST"),
            f"{total_shopping} shopping item(s); {remaining_lines} with remaining quantities across {unresolved_materials} projects.", "/records"),
        GoblinCheck("Patch", "LABOUR RECORDED" if total_labor_logs else "NO LABOUR LOGS",
            f"{total_labor_logs} work log(s), {hours} user-entered hours. Work order tracking is not implemented.", "/records"),
        GoblinCheck("Squarmish", "DRAFTS FOR REVIEW" if draft_count else
            ("OUTSTANDING" if ledger.outstanding > 0 else "NO DRAFTS"),
            f"{len(all_invoices)} invoice record(s), {draft_count} draft(s); {currency} {ledger.outstanding:.2f} outstanding on approved/issued invoices.", "/squarmish/"),
        GoblinCheck("Grimscratch", "NOT AUTOMATED",
            "Compliance/risk review is not instrumented. No clearance is implied.", "/workflows/grimscratch"),
    )
    resolved_view, interpretation = resolve_view(view, question)
    return CommandBriefing(
        business_name=business.name, currency=currency, project=selected,
        projects=all_projects, project_brief=selected_brief,
        portfolio_checks=portfolio_checks, ledger=ledger, actual_hours=hours,
        project_count=len(all_projects),
        active_count=sum(p.status == RecordStatus.ACTIVE for p in all_projects),
        completed_count=sum(p.status == RecordStatus.COMPLETED for p in all_projects),
        archived_count=sum(p.status == RecordStatus.ARCHIVED for p in all_projects),
        actions=actions, view=resolved_view, question=(question or "").strip()[:180],
        interpretation=interpretation,
    )
