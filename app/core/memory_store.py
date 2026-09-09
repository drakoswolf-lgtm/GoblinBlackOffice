"""In-memory Black Office persistence for tests and local integration work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .models import Agreement, Business, Client, Expense, Invoice, Payment, Project

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self, id_getter: Callable[[T], str]) -> None:
        self._id_getter = id_getter
        self._records: dict[str, T] = {}

    def save(self, record: T) -> T:
        self._records[self._id_getter(record)] = record
        return record

    def get(self, record_id: str, business_id: str | None = None) -> T | None:
        record = self._records.get(record_id)
        if record is None:
            return None
        if business_id is not None and getattr(record, "business_id", None) != business_id:
            return None
        return record

    def list_for_business(self, business_id: str) -> list[T]:
        return [
            record
            for record in self._records.values()
            if getattr(record, "business_id", None) == business_id
        ]


@dataclass
class InMemoryBlackOfficeStore:
    """Concrete dependency-free store implementing the shared repository shape."""

    businesses: InMemoryRepository[Business]
    clients: InMemoryRepository[Client]
    projects: InMemoryRepository[Project]
    agreements: InMemoryRepository[Agreement]
    expenses: InMemoryRepository[Expense]
    invoices: InMemoryRepository[Invoice]
    payments: InMemoryRepository[Payment]

    @classmethod
    def create(cls) -> "InMemoryBlackOfficeStore":
        return cls(
            businesses=InMemoryRepository(lambda item: item.business_id),
            clients=InMemoryRepository(lambda item: item.client_id),
            projects=InMemoryRepository(lambda item: item.project_id),
            agreements=InMemoryRepository(lambda item: item.agreement_id),
            expenses=InMemoryRepository(lambda item: item.expense_id),
            invoices=InMemoryRepository(lambda item: item.invoice_id),
            payments=InMemoryRepository(lambda item: item.payment_id),
        )
