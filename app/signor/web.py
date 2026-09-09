"""SigNor v0.1 web surface."""

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import os
from flask import Flask, redirect, render_template, request, send_file, url_for

from app.core.documents import build_agreement_pdf
from app.core.models import AgreementStatus
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
    active_business_id = _business_id()
    projects = _store.projects.list_for_business(active_business_id)
    clients = {c.client_id: c for c in _store.clients.list_for_business(active_business_id)}
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
            business_id=active_business_id,
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
        projects=projects,
        clients=clients,
    )


@app.route("/agreements/<agreement_id>/pdf", methods=["GET"])
def agreement_pdf(agreement_id: str):
    active_business_id = _business_id()
    agreement = _store.agreements.get(agreement_id, active_business_id)
    business = _store.businesses.get(active_business_id, active_business_id)
    if agreement is None or business is None:
        return ("Agreement not found.", 404)
    project = _store.projects.get(agreement.project_id, active_business_id)
    client = _store.clients.get(project.client_id, active_business_id) if project is not None and project.client_id else None
    pdf = build_agreement_pdf(business=business, agreement=agreement, project=project, client=client)
    return send_file(BytesIO(pdf), mimetype="application/pdf", as_attachment=True, download_name=f"{agreement.agreement_id}.pdf")


@app.route("/agreements/<agreement_id>/confirm", methods=["POST"])
def confirm_agreement(agreement_id: str):
    active_business_id = _business_id()
    agreement = _store.agreements.get(agreement_id, active_business_id)
    if agreement is None:
        return ("Agreement not found.", 404)
    if agreement.status != AgreementStatus.DRAFT:
        return ("Only draft agreements can be confirmed.", 409)
    _store.agreements.save(replace(agreement, status=AgreementStatus.PROPOSED))
    return redirect(url_for("agreement_pdf", agreement_id=agreement_id))
