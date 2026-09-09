"""Persistence boundaries for shared Black Office records.

These protocols keep goblin workflows independent of the storage engine. The
first production implementation can use PostgreSQL while tests and local tools
can provide lightweight alternatives.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from .models import Agreement, Business, Client, Expense, Invoice, Payment, Project

T = TypeVar("T")


class Repository(Protocol[T]):
    def save(self, record: T) -> T: ...
    def get(self, record_id: str) -> T | None: ...
    def list_for_business(self, business_id: str) -> list[T]: ...


class BlackOfficeStore(Protocol):
    """Storage contract shared by Æterna and every goblin specialist."""

    businesses: Repository[Business]
    clients: Repository[Client]
    projects: Repository[Project]
    agreements: Repository[Agreement]
    expenses: Repository[Expense]
    invoices: Repository[Invoice]
    payments: Repository[Payment]
