"""Persistence boundaries for shared Black Office records."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .models import (
    Agreement,
    Business,
    ChangeOrder,
    Client,
    Estimate,
    Expense,
    Invoice,
    MaterialPlan,
    Payment,
    Project,
    ShoppingListItem,
    User,
    WorkLog,
)

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
    estimates: Repository[Estimate]
    material_plans: Repository[MaterialPlan]
    shopping_items: Repository[ShoppingListItem]
    work_logs: Repository[WorkLog]
    change_orders: Repository[ChangeOrder]
    expenses: Repository[Expense]
    invoices: Repository[Invoice]
    payments: Repository[Payment]
