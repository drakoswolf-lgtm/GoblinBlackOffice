"""Æterna-led Black Office application shell."""
from __future__ import annotations
import hmac
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from flask import Flask, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app.core.job_lifecycle import (
    draft_job_plan,
    draft_project_invoice,
    persist_job_plan,
    record_payment,
    record_project_work,
)
from app.core.ledger import summarize_project_ledger
from app.core.runtime import office_store
from app.ledgergut.web import app as ledgergut_app
from app.signor.web import app as signor_app
from app.squarmish.web import app as squarmish_app
from app.office.auth import (
    authenticate,
    complete_onboarding,
    configure_same_origin_protection,
    current_business_id,
    current_user,
    register_user,
    sign_in,
)
from app.office.records import create_client, create_project
from app.office.grunts import grunt_workflow
from app.packrat.service import MaterialRequirementInput

_auth_required = os.environ.get("GBO_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}
_secret = os.environ.get("GBO_SECRET", "").strip()
_invite_token = os.environ.get("GBO_INVITE_TOKEN", "").strip()
if _auth_required and not _secret:
    raise RuntimeError("GBO_SECRET is required when authentication is enabled.")

office_app = Flask(__name__, template_folder="templates")
office_app.secret_key = _secret or "gbo-dev-secret"
office_app.config["SESSION_COOKIE_NAME"] = "gbo_session"
office_app.config["SESSION_COOKIE_HTTPONLY"] = True
office_app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
office_app.config["SESSION_COOKIE_SECURE"] = _auth_required
office_app.config["GBO_AUTH_REQUIRED"] = _auth_required
office_app.config["GBO_INVITE_TOKEN"] = _invite_token
configure_same_origin_protection(office_app)

_canon_root = Path(__file__).resolve().parents[2] / "resources" / "canon"

def _sticky_payload():
    from app.office.loading_sticky import LOAD_BEARING_STICKY_LINES
    return [
        {"text": line.text, "min": line.min_progress, "max": line.max_progress, "weight": line.weight}
        for line in LOAD_BEARING_STICKY_LINES
    ]


def _parse_material_requirements(raw: str):
    requirements = []
    errors = []
    for number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2 or len(parts) > 4:
            errors.append(
                f"Material line {number}: use description | quantity | unit | estimated unit cost."
            )
            continue
        description = parts[0]
        quantity = parts[1]
        unit = parts[2] if len(parts) >= 3 and parts[2] else "ea"
        cost = parts[3] if len(parts) >= 4 and parts[3] else None
        try:
            requirements.append(
                MaterialRequirementInput(
                    description=description,
                    quantity=quantity,
                    unit=unit,
                    estimated_unit_cost=cost,
                )
            )
        except ValueError as exc:
            errors.append(f"Material line {number}: {exc}")
    if not requirements and not errors:
        errors.append("Add at least one material line for this beta planning pass.")
    return tuple(requirements), tuple(errors)


def _parse_optional_date(raw: str):
    value = raw.strip()
    if not value:
        return None, None
    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, "Enter a valid date."

@office_app.before_request
def _office_auth_gate():
    if not office_app.config.get("GBO_AUTH_REQUIRED", False): return None
    if request.endpoint in {"login", "register", "health", "static"}: return None
    user = current_user()
    if user is None: return redirect(url_for("login", next=request.path))
    if not user.onboarding_complete and request.endpoint not in {"onboarding", "logout"}: return redirect(url_for("onboarding"))
    return None

@office_app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = authenticate(request.form.get("email", ""), request.form.get("password", ""))
        if user is None: error = "Email or password not recognized."
        else:
            sign_in(user)
            return redirect(url_for("onboarding" if not user.onboarding_complete else "index"))
    return render_template("office/login.html", error=error)

@office_app.route("/register", methods=["GET", "POST"])
def register():
    errors = ()
    invite_required = bool(office_app.config.get("GBO_INVITE_TOKEN", ""))
    if request.method == "POST":
        configured_invite = str(office_app.config.get("GBO_INVITE_TOKEN", ""))
        supplied_invite = request.form.get("invite_code", "").strip()
        if configured_invite and not hmac.compare_digest(configured_invite, supplied_invite):
            errors = ("A valid private-beta invite code is required.",)
        else:
            user, errors = register_user(email=request.form.get("email", ""), password=request.form.get("password", ""), display_name=request.form.get("display_name", ""))
            if user is not None:
                sign_in(user)
                return redirect(url_for("onboarding"))
    return render_template("office/register.html", errors=errors, invite_required=invite_required)

@office_app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    user = current_user()
    if user is None: return redirect(url_for("login"))
    errors = ()
    if request.method == "POST":
        updated, errors = complete_onboarding(
            user,
            business_name=request.form.get("business_name", ""),
            currency=request.form.get("currency", "CAD"),
            operating_name=request.form.get("operating_name", ""),
            business_type=request.form.get("business_type", ""),
            legal_structure=request.form.get("legal_structure", ""),
            operating_model=request.form.get("operating_model", ""),
            address_line1=request.form.get("address_line1", ""),
            address_line2=request.form.get("address_line2", ""),
            city=request.form.get("city", ""),
            region=request.form.get("region", ""),
            postal_code=request.form.get("postal_code", ""),
            country=request.form.get("country", ""),
            website=request.form.get("website", ""),
            service_area=request.form.get("service_area", ""),
            business_phone=request.form.get("business_phone", ""),
            business_email=request.form.get("business_email", ""),
            parent_business_name=request.form.get("parent_business_name", ""),
            subsidiaries=request.form.get("subsidiaries", ""),
            franchise_status=request.form.get("franchise_status", ""),
            franchisor_name=request.form.get("franchisor_name", ""),
            fiscal_year_end=request.form.get("fiscal_year_end", ""),
            tax_registration_status=request.form.get("tax_registration_status", ""),
            gst_hst_number=request.form.get("gst_hst_number", ""),
            provincial_tax_number=request.form.get("provincial_tax_number", ""),
            tax_notes=request.form.get("tax_notes", ""),
            payment_terms=request.form.get("payment_terms", ""),
            workforce_model=request.form.get("workforce_model", ""),
            accounting_platform=request.form.get("accounting_platform", ""),
            typical_services=request.form.get("typical_services", ""),
        )
        if updated is not None: return redirect(url_for("index"))
    return render_template("office/onboarding.html", user=user, errors=errors, sticky_lines=_sticky_payload())

@office_app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@office_app.route("/records", methods=["GET", "POST"])
def record_desk():
    bid = current_business_id()
    errors = ()
    if request.method == "POST":
        if request.form.get("kind") == "client":
            _, errors = create_client(business_id=bid, name=request.form.get("name", ""), email=request.form.get("email", ""), phone=request.form.get("phone", ""))
        elif request.form.get("kind") == "project":
            _, errors = create_project(business_id=bid, client_id=request.form.get("client_id", ""), name=request.form.get("name", ""), description=request.form.get("description", ""))
        if not errors: return redirect(url_for("record_desk"))
    return render_template("office/records.html", errors=errors, clients=office_store.clients.list_for_business(bid), projects=office_store.projects.list_for_business(bid))

@office_app.route("/jobs/new", methods=["GET", "POST"])
def new_job():
    bid = current_business_id()
    errors = ()
    if request.method == "POST":
        selected_client_id = request.form.get("client_id", "").strip()
        client_id = selected_client_id
        if not client_id:
            client, client_errors = create_client(
                business_id=bid,
                name=request.form.get("client_name", ""),
                email=request.form.get("client_email", ""),
                phone=request.form.get("client_phone", ""),
            )
            if client is None:
                errors = client_errors
            else:
                client_id = client.client_id
        elif office_store.clients.get(client_id, bid) is None:
            errors = ("Choose a valid client from this Office.",)

        if not errors:
            project, project_errors = create_project(
                business_id=bid,
                client_id=client_id,
                name=request.form.get("project_name", ""),
                description=request.form.get("description", ""),
            )
            if project is not None:
                return redirect(url_for("job_workbench", project_id=project.project_id))
            errors = project_errors

    return render_template(
        "office/new_job.html",
        errors=errors,
        clients=office_store.clients.list_for_business(bid),
        form_data=request.form if request.method == "POST" else {},
    )


@office_app.route("/jobs/<project_id>", methods=["GET", "POST"])
def job_workbench(project_id: str):
    bid = current_business_id()
    project = office_store.projects.get(project_id, bid)
    if project is None:
        return ("Project not found.", 404)

    errors = []
    message = request.args.get("message", "").strip()

    if request.method == "POST":
        action = request.form.get("action", "").strip()

        if action == "plan":
            agreement = office_store.agreements.get(request.form.get("agreement_id", "").strip(), bid)
            if agreement is None or agreement.project_id != project_id:
                errors.append("Choose an agreement for this project.")
            requirements, material_errors = _parse_material_requirements(
                request.form.get("materials_text", "")
            )
            errors.extend(material_errors)
            if not errors and agreement is not None:
                draft = draft_job_plan(
                    business_id=bid,
                    agreement=agreement,
                    labour_hours=request.form.get("labour_hours", ""),
                    labour_rate=request.form.get("labour_rate", ""),
                    materials=requirements,
                    other_cost=request.form.get("other_cost", "0"),
                    assumptions=request.form.get("assumptions", ""),
                )
                errors.extend(draft.errors)
                if not errors:
                    persist_job_plan(
                        office_store,
                        draft,
                        approve_materials=request.form.get("approve_materials") == "1",
                    )
                    return redirect(url_for("job_workbench", project_id=project_id, message="plan-saved"))

        elif action == "work":
            occurred_on, date_error = _parse_optional_date(request.form.get("occurred_on", ""))
            if date_error:
                errors.append(date_error)
            if not errors:
                result = record_project_work(
                    office_store,
                    business_id=bid,
                    project_id=project_id,
                    description=request.form.get("description", ""),
                    hours=request.form.get("hours", ""),
                    occurred_on=occurred_on,
                    billable=request.form.get("billable") == "1",
                    rate_override=request.form.get("rate_override", ""),
                )
                errors.extend(result.errors)
                if not errors:
                    return redirect(url_for("job_workbench", project_id=project_id, message="work-saved"))

        elif action == "invoice":
            agreement = office_store.agreements.get(request.form.get("agreement_id", "").strip(), bid)
            if agreement is None or agreement.project_id != project_id:
                errors.append("Choose an agreement for this project.")
            due_date, date_error = _parse_optional_date(request.form.get("due_date", ""))
            if date_error:
                errors.append(date_error)
            if not errors and agreement is not None:
                result = draft_project_invoice(
                    office_store,
                    business_id=bid,
                    agreement=agreement,
                    client_id=project.client_id or "",
                    labour_rate=request.form.get("labour_rate", ""),
                    include_agreement_amount=request.form.get("include_agreement_amount") == "1",
                    due_date=due_date,
                )
                errors.extend(result.errors)
                if not errors:
                    return redirect(url_for("job_workbench", project_id=project_id, message="invoice-drafted"))

        elif action == "payment":
            invoice = office_store.invoices.get(request.form.get("invoice_id", "").strip(), bid)
            if invoice is None or invoice.project_id != project_id:
                errors.append("Choose an invoice for this project.")
            received_on, date_error = _parse_optional_date(request.form.get("received_on", ""))
            if date_error:
                errors.append(date_error)
            if not errors and invoice is not None:
                try:
                    record_payment(
                        office_store,
                        invoice=invoice,
                        amount=request.form.get("amount", ""),
                        received_on=received_on,
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                if not errors:
                    return redirect(url_for("job_workbench", project_id=project_id, message="payment-recorded"))
        else:
            errors.append("Unknown job action.")

    client = office_store.clients.get(project.client_id, bid) if project.client_id else None
    business = office_store.businesses.get(bid, bid)
    agreements = [a for a in office_store.agreements.list_for_business(bid) if a.project_id == project_id]
    estimates = [e for e in office_store.estimates.list_for_business(bid) if e.project_id == project_id]
    material_plans = [p for p in office_store.material_plans.list_for_business(bid) if p.project_id == project_id]
    shopping_items = [i for i in office_store.shopping_items.list_for_business(bid) if i.project_id == project_id]
    work_logs = [w for w in office_store.work_logs.list_for_business(bid) if w.project_id == project_id]
    expenses = [e for e in office_store.expenses.list_for_business(bid) if e.project_id == project_id]
    invoices = [i for i in office_store.invoices.list_for_business(bid) if i.project_id == project_id]
    payments = tuple(office_store.payments.list_for_business(bid))
    currency = business.reporting_currency if business is not None else "CAD"
    ledger = summarize_project_ledger(
        business_id=bid,
        project_id=project_id,
        invoices=tuple(invoices),
        payments=payments,
        expenses=tuple(expenses),
        currency=currency,
    )
    actual_hours = sum((log.hours for log in work_logs), Decimal("0"))
    expense_total = sum((expense.amount for expense in expenses if expense.currency.upper() == currency.upper()), Decimal("0.00"))

    message_text = {
        "agreement-ready": "Agreement marked ready to present. PDF remains available here.",
        "plan-saved": "Estimate and material plan saved. Packrat has the shopping list.",
        "work-saved": "Actual labour recorded.",
        "invoice-drafted": "Invoice draft created. Review it before issuing.",
        "invoice-approved": "Invoice approved for issuing. PDF remains available here.",
        "payment-recorded": "Payment recorded and ledger updated.",
    }.get(message, "")

    return render_template(
        "office/job_workbench.html",
        project=project,
        client=client,
        agreements=agreements,
        estimates=estimates,
        latest_estimate=estimates[-1] if estimates else None,
        material_plans=material_plans,
        shopping_items=shopping_items,
        work_logs=work_logs,
        expenses=expenses,
        invoices=invoices,
        ledger=ledger,
        actual_hours=actual_hours,
        expense_total=expense_total,
        currency=currency,
        errors=tuple(errors),
        message=message_text,
    )


@office_app.route("/workflows/<grunt_id>")
def grunt_workflow_page(grunt_id: str):
    grunt = grunt_workflow(grunt_id)
    if grunt is None:
        return ("Workflow not found.", 404)
    return render_template("office/grunt_workflow.html", grunt=grunt)

@office_app.route("/")
def index():
    bid = current_business_id()
    projects = office_store.projects.list_for_business(bid)
    clients = {client.client_id: client for client in office_store.clients.list_for_business(bid)}
    specialists = [
        {"name":"Ledgergut","role":"Receipts & expenses","status":"live","href":"/ledgergut/","note":"Feed me the receipt. Keep your fingers."},
        {"name":"SigNor","role":"Agreements & scope","status":"live","href":"/signor/","note":"Words matter. Especially the ones someone forgot to define."},
        {"name":"Squarmish","role":"Invoices & receivables","status":"live","href":"/squarmish/","note":"Completed work is lovely. Paid work is lovelier."},
        {"name":"Packrat McDuffel","role":"Logistics & materials","status":"rough-in","href":"/workflows/packrat","note":"Right thing, right place, ideally before someone needs it."},
        {"name":"Patch","role":"Operations & work orders","status":"rough-in","href":"/workflows/patch","note":"Loose ends become work orders. Work orders become finished work."},
        {"name":"Grimscratch","role":"Risk & compliance","status":"rough-in","href":"/workflows/grimscratch","note":"Find the expensive assumption before it becomes an expensive fact."},
    ]
    return render_template(
        "office/index.html",
        specialists=specialists,
        projects=projects,
        clients=clients,
        user=current_user(),
        sticky_lines=_sticky_payload(),
    )

@office_app.route("/canon/<path:asset_path>")
def canon_asset(asset_path: str):
    return send_from_directory(_canon_root, asset_path)

@office_app.route("/health")
def health(): return {"status":"ok","service":"goblin-black-office"}

application = DispatcherMiddleware(office_app,{"/ledgergut":ledgergut_app,"/signor":signor_app,"/squarmish":squarmish_app})
