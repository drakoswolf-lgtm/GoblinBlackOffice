"""SigNor v0.1 web surface."""

from __future__ import annotations

import os
from flask import Flask, render_template, request

from app.core.runtime import business_id, office_store
from app.office.auth import configure_specialist_auth, current_business_id
from app.signor.service import AgreementDraftInput, draft_agreement

app = Flask(__name__, template_folder="templates")
app.config["GBO_AUTH_REQUIRED"] = os.environ.get("GBO_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}
configure_specialist_auth(app)
_store = office_store


def _business_id() -> str:
    return current_business_id() if app.config.get("GBO_AUTH_REQUIRED") else business_id


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

    return render_template("signor/index.html", form_data=form_data, errors=errors, agreement=agreement)
