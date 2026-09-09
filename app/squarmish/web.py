"""Squarmish v0.1 web surface."""

from __future__ import annotations

from datetime import date

from flask import Flask, render_template, request

from app.core.runtime import business_id, office_store
from app.squarmish.service import draft_invoice

app = Flask(__name__, template_folder="templates")
_store = office_store


@app.route("/", methods=["GET", "POST"])
def index():
    agreements = _store.agreements.list_for_business(business_id)
    expenses = _store.expenses.list_for_business(business_id)
    result = None

    if request.method == "POST":
        agreement_id = request.form.get("agreement_id", "")
        agreement = _store.agreements.get(agreement_id)
        if agreement is None:
            result = type("MissingResult", (), {"invoice": None, "lines": (), "errors": ("Select a valid agreement.",), "review_notes": ()})()
        else:
            selected_ids = set(request.form.getlist("expense_id"))
            selected_expenses = tuple(exp for exp in expenses if exp.expense_id in selected_ids)
            due_raw = request.form.get("due_date", "").strip()
            due_date = date.fromisoformat(due_raw) if due_raw else None
            result = draft_invoice(
                business_id=business_id,
                agreement=agreement,
                client_id=request.form.get("client_id", ""),
                expenses=selected_expenses,
                include_agreement_amount=request.form.get("include_agreement_amount") == "1",
                due_date=due_date,
            )
            if result.invoice is not None:
                _store.invoices.save(result.invoice)

    return render_template(
        "squarmish/index.html",
        agreements=agreements,
        expenses=expenses,
        result=result,
    )
