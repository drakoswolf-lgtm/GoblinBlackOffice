"""Persistence boundaries for shared Black Office records."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .models import Agreement, Business, Client, Expense, Invoice, Payment, Project, User

T = TypeVar("T")


class Repository(Protocol[T]):
    def save(self, record: T) -> T: ...
    def get(self, record_id: str, business_id: str | None = None) -> T | None: ...
    def list_for_business(self, business_id: str) -> list[T]: ...


class BlackOfficeStore(Protocol):
    users: Repository[User]
    businesses: Repository[Business]
    clients: Repository[Client]
    projects: Repository[Project]
    agreements: Repository[Agreement]
    expenses: Repository[Expense]
    invoices: Repository[Invoice]
    payments: Repository[Payment]
