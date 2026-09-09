"""Squarmish v0.1 web surface."""

from __future__ import annotations

from datetime import date
import os

from flask import Flask, render_template, request

from app.core.runtime import business_id, office_store
from app.office.auth import configure_specialist_auth, current_business_id
from app.squarmish.service import draft_invoice

app = Flask(__name__, template_folder="templates")
app.config["GBO_AUTH_REQUIRED"] = os.environ.get("GBO_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}
configure_specialist_auth(app)
_store = office_store


def _business_id() -> str:
    return current_business_id() if app.config.get("GBO_AUTH_REQUIRED") else business_id


@app.route("/", methods=["GET", "POST"])
def index():
    active_business_id = _business_id()
    agreements = _store.agreements.list_for_business(active_business_id)
    expenses = _store.expenses.list_for_business(active_business_id)
    result = None

    if request.method == "POST":
        agreement_id = request.form.get("agreement_id", "")
        agreement = _store.agreements.get(agreement_id, active_business_id)
        if agreement is None:
            result = type("MissingResult", (), {"invoice": None, "lines": (), "errors": ("Select a valid agreement.",), "review_notes": ()})()
        else:
            selected_ids = set(request.form.getlist("expense_id"))
            selected_expenses = tuple(exp for exp in expenses if exp.expense_id in selected_ids)
            due_raw = request.form.get("due_date", "").strip()
            try:
                due_date = date.fromisoformat(due_raw) if due_raw else None
            except ValueError:
                result = type("InvalidDateResult", (), {"invoice": None, "lines": (), "errors": ("Enter a valid due date.",), "review_notes": ()})()
            else:
                result = draft_invoice(
                    business_id=active_business_id,
                    agreement=agreement,
                    client_id=request.form.get("client_id", ""),
                    expenses=selected_expenses,
                    include_agreement_amount=request.form.get("include_agreement_amount") == "1",
                    due_date=due_date,
                )
                if result.invoice is not None:
                    _store.invoices.save(result.invoice)

    return render_template("squarmish/index.html", agreements=agreements, expenses=expenses, result=result)
