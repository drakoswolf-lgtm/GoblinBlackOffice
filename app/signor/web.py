"""SigNor v0.1 web surface."""

from __future__ import annotations

import os

from flask import Flask, render_template, request

from app.core.memory_store import InMemoryBlackOfficeStore
from app.signor.service import AgreementDraftInput, draft_agreement

app = Flask(__name__, template_folder="templates")
_store = InMemoryBlackOfficeStore.create()


def _business_id() -> str:
    return os.environ.get("GBO_BUSINESS_ID", "local-development")


@app.route("/", methods=["GET", "POST"])
def index():
    form_data: dict[str, str] = {}
    errors: tuple[str, ...] = ()
    agreement = None

    if request.method == "POST":
        form_data = request.form.to_dict()
        result = draft_agreement(
            AgreementDraftInput(
                project_id=form_data.get("project_id", ""),
                title=form_data.get("title", ""),
                scope=form_data.get("scope", ""),
                amount=form_data.get("amount", ""),
                currency=form_data.get("currency", "CAD"),
                assumptions=form_data.get("assumptions", ""),
                exclusions=form_data.get("exclusions", ""),
                payment_terms=form_data.get("payment_terms", ""),
                change_order_terms=form_data.get("change_order_terms", ""),
            ),
            business_id=_business_id(),
        )
        errors = result.errors
        agreement = result.agreement
        if agreement is not None:
            _store.agreements.save(agreement)

    return render_template(
        "signor/index.html",
        form_data=form_data,
        errors=errors,
        agreement=agreement,
    )
