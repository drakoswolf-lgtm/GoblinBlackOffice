"""SigNor agreement drafting service.

SigNor turns explicit human inputs into a shared Black Office Agreement. He does
not infer missing commercial terms. Ambiguity is returned to the human instead.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.core.models import Agreement, AgreementStatus


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
