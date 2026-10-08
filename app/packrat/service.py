"""Packrat material planning and shopping-list reconciliation.

Packrat is conservative by design: receipt lines are only auto-matched when a
single shopping-list item is a strong textual match. Ambiguous purchases stay
visible for human confirmation rather than quietly corrupting job quantities.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
import re
import uuid

from app.core.models import MaterialPlan, ShoppingListItem
from app.ledgergut.models import ReceiptRecord


def _decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _match_score(left: str, right: str) -> float:
    a, b = _normalize(left), _normalize(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.92
    at, bt = set(a.split()), set(b.split())
    overlap = len(at & bt)
    return overlap / max(len(at), len(bt)) if overlap else 0.0


@dataclass(frozen=True)
class MaterialRequirementInput:
    description: str
    quantity: Decimal | int | float | str
    unit: str = "ea"
    estimated_unit_cost: Decimal | int | float | str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        quantity = _decimal(self.quantity, "quantity")
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        object.__setattr__(self, "quantity", quantity)
        if self.estimated_unit_cost is not None:
            cost = _decimal(self.estimated_unit_cost, "estimated_unit_cost")
            if cost < 0:
                raise ValueError("estimated_unit_cost cannot be negative")
            object.__setattr__(self, "estimated_unit_cost", cost)


@dataclass(frozen=True)
class MaterialPlanDraftResult:
    plan: MaterialPlan | None
    items: tuple[ShoppingListItem, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ReceiptMatch:
    receipt_line: str
    shopping_item_id: str
    quantity: Decimal
    amount: Decimal


@dataclass(frozen=True)
class ReceiptReconciliation:
    items: tuple[ShoppingListItem, ...]
    matches: tuple[ReceiptMatch, ...]
    unresolved_lines: tuple[str, ...]


def draft_material_plan(
    *,
    business_id: str,
    project_id: str,
    title: str,
    requirements: tuple[MaterialRequirementInput, ...],
    agreement_id: str | None = None,
    estimate_id: str | None = None,
    notes: str = "",
) -> MaterialPlanDraftResult:
    errors: list[str] = []
    if not business_id.strip():
        errors.append("Business is required.")
    if not project_id.strip():
        errors.append("Project is required.")
    if not title.strip():
        errors.append("Material plan title is required.")
    if not requirements:
        errors.append("At least one material requirement is required.")
    if errors:
        return MaterialPlanDraftResult(None, (), tuple(errors))

    plan_id = f"MAT-{uuid.uuid4().hex[:12].upper()}"
    plan = MaterialPlan(
        material_plan_id=plan_id,
        business_id=business_id.strip(),
        project_id=project_id.strip(),
        agreement_id=agreement_id,
        estimate_id=estimate_id,
        title=title.strip(),
        notes=notes.strip(),
    )
    items = tuple(
        ShoppingListItem(
            shopping_item_id=f"SHOP-{uuid.uuid4().hex[:12].upper()}",
            business_id=business_id.strip(),
            project_id=project_id.strip(),
            material_plan_id=plan_id,
            description=req.description.strip(),
            quantity_required=req.quantity,
            unit=req.unit.strip() or "ea",
            estimated_unit_cost=req.estimated_unit_cost,
            notes=req.notes.strip(),
        )
        for req in requirements
    )
    return MaterialPlanDraftResult(plan, items, ())


def reconcile_receipt(
    record: ReceiptRecord,
    shopping_items: tuple[ShoppingListItem, ...],
    *,
    minimum_score: float = 0.75,
) -> ReceiptReconciliation:
    """Apply confidently matched receipt lines to shopping-list actuals.

    A line is auto-applied only when the best match clears ``minimum_score`` and
    is meaningfully better than the runner-up. Everything else is returned in
    ``unresolved_lines`` for human review.
    """
    if not record.record_id:
        raise ValueError("receipt record_id is required for reconciliation")

    current = {item.shopping_item_id: item for item in shopping_items}
    matches: list[ReceiptMatch] = []
    unresolved: list[str] = []

    for line in record.receipt.line_items:
        candidates: list[tuple[float, ShoppingListItem]] = []
        for item in current.values():
            score = _match_score(line.name, item.description)
            if score > 0:
                candidates.append((score, item))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        if not candidates:
            unresolved.append(line.name)
            continue

        best_score, best = candidates[0]
        runner_score = candidates[1][0] if len(candidates) > 1 else 0.0
        if best_score < minimum_score or (runner_score and best_score - runner_score < 0.15):
            unresolved.append(line.name)
            continue

        quantity = Decimal(line.quantity)
        amount = (quantity * Decimal(line.unit_price)).quantize(Decimal("0.01"))
        receipt_ids = [part for part in best.source_receipt_ids.split(",") if part]
        if record.record_id not in receipt_ids:
            receipt_ids.append(record.record_id)
        updated = replace(
            best,
            quantity_acquired=best.quantity_acquired + quantity,
            actual_cost=(best.actual_cost + amount).quantize(Decimal("0.01")),
            source_receipt_ids=",".join(receipt_ids),
        )
        current[best.shopping_item_id] = updated
        matches.append(
            ReceiptMatch(
                receipt_line=line.name,
                shopping_item_id=best.shopping_item_id,
                quantity=quantity,
                amount=amount,
            )
        )

    return ReceiptReconciliation(
        items=tuple(current[item.shopping_item_id] for item in shopping_items),
        matches=tuple(matches),
        unresolved_lines=tuple(unresolved),
    )
