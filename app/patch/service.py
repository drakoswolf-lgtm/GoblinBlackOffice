"""Patch work execution services.

Patch records actual labour only when a human supplies it. Estimated time and
actual time remain separate so the Office can compare them without quietly
turning guesses into billable facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import uuid

from app.core.models import WorkLog


def _decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number") from exc


@dataclass(frozen=True)
class WorkLogResult:
    work_log: WorkLog | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class LabourSummary:
    hours: Decimal
    amount: Decimal
    currency: str
    unpriced_hours: Decimal = Decimal("0")


def record_work(
    *,
    business_id: str,
    project_id: str,
    description: str,
    hours: Decimal | int | float | str,
    occurred_on: date | None = None,
    billable: bool = True,
    rate_override: Decimal | int | float | str | None = None,
) -> WorkLogResult:
    errors: list[str] = []
    if not business_id.strip():
        errors.append("Business is required.")
    if not project_id.strip():
        errors.append("Project is required.")
    if not description.strip():
        errors.append("Work description is required.")

    try:
        parsed_hours = _decimal(hours, "hours")
        if parsed_hours <= 0:
            errors.append("Hours must be greater than zero.")
    except ValueError as exc:
        parsed_hours = Decimal("0")
        errors.append(str(exc))

    parsed_rate: Decimal | None = None
    if rate_override is not None and str(rate_override).strip() != "":
        try:
            parsed_rate = _decimal(rate_override, "rate_override")
            if parsed_rate < 0:
                errors.append("Rate override cannot be negative.")
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        return WorkLogResult(None, tuple(errors))

    return WorkLogResult(
        WorkLog(
            work_log_id=f"WORK-{uuid.uuid4().hex[:12].upper()}",
            business_id=business_id.strip(),
            project_id=project_id.strip(),
            description=description.strip(),
            hours=parsed_hours,
            occurred_on=occurred_on,
            billable=billable,
            rate_override=parsed_rate,
        ),
        (),
    )


def summarize_labour(
    work_logs: tuple[WorkLog, ...],
    *,
    default_rate: Decimal | int | float | str | None,
    currency: str = "CAD",
) -> LabourSummary:
    default = None if default_rate is None or str(default_rate).strip() == "" else _decimal(default_rate, "default_rate")
    hours = Decimal("0")
    amount = Decimal("0.00")
    unpriced = Decimal("0")
    for log in work_logs:
        if not log.billable:
            continue
        hours += log.hours
        rate = log.rate_override if log.rate_override is not None else default
        if rate is None:
            unpriced += log.hours
            continue
        amount += log.hours * rate
    return LabourSummary(
        hours=hours,
        amount=amount.quantize(Decimal("0.01")),
        currency=currency.upper(),
        unpriced_hours=unpriced,
    )
