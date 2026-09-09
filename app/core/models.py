"""Shared Black Office domain models.

The Black Office owns business data. Goblins operate on these shared records
rather than maintaining isolated copies of clients, projects, agreements,
expenses, invoices, and payments.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class RecordStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AgreementStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    SUPERSEDED = "superseded"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    DUE = "due"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


@dataclass(frozen=True)
class User:
    user_id: str
    business_id: str
    email: str
    password_hash: str
    display_name: str
    onboarding_complete: bool = False
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Business:
    business_id: str
    name: str
    reporting_currency: str = "CAD"
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Client:
    client_id: str
    business_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Project:
    project_id: str
    business_id: str
    client_id: str | None
    name: str
    description: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


@dataclass(frozen=True)
class Agreement:
    agreement_id: str
    business_id: str
    project_id: str
    title: str
    scope: str
    amount: Decimal | None = None
    currency: str = "CAD"
    status: AgreementStatus = AgreementStatus.DRAFT


@dataclass(frozen=True)
class Expense:
    expense_id: str
    business_id: str
    project_id: str | None
    amount: Decimal
    currency: str
    description: str
    source_goblin: str = "ledgergut"
    source_record_id: str | None = None
    occurred_on: date | None = None
    billable: bool | None = None


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    business_id: str
    project_id: str
    client_id: str
    total: Decimal
    currency: str = "CAD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: date | None = None


@dataclass(frozen=True)
class Payment:
    payment_id: str
    business_id: str
    invoice_id: str
    amount: Decimal
    currency: str = "CAD"
    received_on: date | None = None
