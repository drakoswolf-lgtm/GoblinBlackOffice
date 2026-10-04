"""SigNor agreement and change-order drafting services.

SigNor turns explicit human inputs into shared Black Office records. He does not
infer missing commercial terms. Ambiguity is returned to the human instead.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.core.models import Agreement, AgreementStatus, ChangeOrder, ChangeOrderStatus


@dataclass(frozen=True)
class AgreementDraftInput:
    project_id: str
    title: str
    scope: str
    amount: str = ""
    currency: str = "CAD"
    assumptions: str = ""
    exclusions: str = ""
    payment_terms: str = ""
    change_order_terms: str = ""


@dataclass(frozen=True)
class AgreementDraftResult:
    agreement: Agreement | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ChangeOrderDraftResult:
    change_order: ChangeOrder | None
    errors: tuple[str, ...]


def draft_agreement(data: AgreementDraftInput, *, business_id: str) -> AgreementDraftResult:
    errors: list[str] = []
    project_id = data.project_id.strip()
    title = data.title.strip()
    scope = data.scope.strip()
    currency = data.currency.strip().upper() or "CAD"

    if not project_id:
        errors.append("Project is required. SigNor will not invent where an agreement belongs.")
    if not title:
        errors.append("Agreement title is required.")
    if not scope:
        errors.append("Scope is required. Expectations deserve names.")

    amount: Decimal | None = None
    if data.amount.strip():
        try:
            amount = Decimal(data.amount.strip()).quantize(Decimal("0.01"))
            if amount < 0:
                errors.append("Price cannot be negative.")
        except InvalidOperation:
            errors.append("Price must be a valid number.")

    if errors:
        return AgreementDraftResult(None, tuple(errors))

    details: list[str] = [scope]
    optional_sections = (
        ("Assumptions", data.assumptions),
        ("Exclusions", data.exclusions),
        ("Payment terms", data.payment_terms),
        ("Change orders", data.change_order_terms),
    )
    for heading, value in optional_sections:
        cleaned = value.strip()
        if cleaned:
            details.append(f"{heading}:\n{cleaned}")

    agreement = Agreement(
        agreement_id=f"AGR-{uuid.uuid4().hex[:12].upper()}",
        business_id=business_id,
        project_id=project_id,
        title=title,
        scope="\n\n".join(details),
        amount=amount,
        currency=currency,
        status=AgreementStatus.DRAFT,
    )
    return AgreementDraftResult(agreement, ())


def draft_change_order(
    *,
    agreement: Agreement,
    business_id: str,
    title: str,
    scope: str,
    amount: str = "",
    currency: str | None = None,
) -> ChangeOrderDraftResult:
    errors: list[str] = []
    if agreement.business_id != business_id:
        errors.append("Agreement does not belong to this business.")
    if not title.strip():
        errors.append("Change-order title is required.")
    if not scope.strip():
        errors.append("Change-order scope is required.")

    parsed_amount: Decimal | None = None
    if amount.strip():
        try:
            parsed_amount = Decimal(amount.strip()).quantize(Decimal("0.01"))
            if parsed_amount < 0:
                errors.append("Change-order amount cannot be negative.")
        except InvalidOperation:
            errors.append("Change-order amount must be a valid number.")

    resolved_currency = (currency or agreement.currency).strip().upper()
    if resolved_currency != agreement.currency.upper():
        errors.append("Change-order currency must match the agreement currency.")

    if errors:
        return ChangeOrderDraftResult(None, tuple(errors))

    return ChangeOrderDraftResult(
        ChangeOrder(
            change_order_id=f"CO-{uuid.uuid4().hex[:12].upper()}",
            business_id=business_id,
            project_id=agreement.project_id,
            agreement_id=agreement.agreement_id,
            title=title.strip(),
            scope=scope.strip(),
            amount=parsed_amount,
            currency=resolved_currency,
            status=ChangeOrderStatus.DRAFT,
        ),
        (),
    )
