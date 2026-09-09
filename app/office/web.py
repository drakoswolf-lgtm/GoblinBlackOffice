"""Æterna-led Black Office application shell."""
from __future__ import annotations
import os
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from app.core.runtime import office_store
from app.ledgergut.web import app as ledgergut_app
from app.signor.web import app as signor_app
from app.squarmish.web import app as squarmish_app
from app.office.auth import authenticate, complete_onboarding, current_business_id, current_user, register_user, sign_in
from app.office.records import create_client, create_project

office_app = Flask(__name__, template_folder="templates")
office_app.secret_key = os.environ.get("GBO_SECRET", "gbo-dev-secret")
office_app.config["SESSION_COOKIE_NAME"] = "gbo_session"
office_app.config["GBO_AUTH_REQUIRED"] = os.environ.get("GBO_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}

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
    if request.method == "POST":
        user, errors = register_user(email=request.form.get("email", ""), password=request.form.get("password", ""), display_name=request.form.get("display_name", ""))
        if user is not None:
            sign_in(user)
            return redirect(url_for("onboarding"))
    return render_template("office/register.html", errors=errors)

@office_app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    user = current_user()
    if user is None: return redirect(url_for("login"))
    errors = ()
    if request.method == "POST":
        updated, errors = complete_onboarding(user, business_name=request.form.get("business_name", ""), currency=request.form.get("currency", "CAD"))
        if updated is not None: return redirect(url_for("index"))
    return render_template("office/onboarding.html", user=user, errors=errors)

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

@office_app.route("/")
def index():
    specialists = [
        {"name":"Ledgergut","role":"Receipts & expenses","status":"live","href":"/ledgergut/","note":"Feed me the receipt. Keep your fingers."},
        {"name":"SigNor","role":"Agreements & scope","status":"live","href":"/signor/","note":"Words matter. Especially the ones someone forgot to define."},
        {"name":"Squarmish","role":"Invoices & receivables","status":"live","href":"/squarmish/","note":"Completed work is lovely. Paid work is lovelier."},
    ]
    return render_template("office/index.html", specialists=specialists, user=current_user())

@office_app.route("/health")
def health(): return {"status":"ok","service":"goblin-black-office"}

application = DispatcherMiddleware(office_app,{"/ledgergut":ledgergut_app,"/signor":signor_app,"/squarmish":squarmish_app})
