"""Office account, session, and onboarding helpers."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
import re
import uuid

from flask import Flask, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.models import Business, User
from app.core.runtime import business_id as fallback_business_id, office_store

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def user_id_for_email(email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:24].upper()
    return f"USR-{digest}"


def register_user(*, email: str, password: str, display_name: str) -> tuple[User | None, tuple[str, ...]]:
    clean_email = email.strip().lower()
    clean_name = display_name.strip()
    errors: list[str] = []
    if not _EMAIL.match(clean_email): errors.append("Enter a valid email address.")
    if len(password) < 10: errors.append("Password must be at least 10 characters.")
    if not clean_name: errors.append("Your name is required.")
    uid = user_id_for_email(clean_email)
    if office_store.users.get(uid) is not None: errors.append("An account already exists for that email.")
    if errors: return None, tuple(errors)

    bid = f"BIZ-{uuid.uuid4().hex[:12].upper()}"
    office_store.businesses.save(Business(business_id=bid, name="New Black Office"))
    user = User(
        user_id=uid,
        business_id=bid,
        email=clean_email,
        password_hash=generate_password_hash(password),
        display_name=clean_name,
    )
    office_store.users.save(user)
    return user, ()


def authenticate(email: str, password: str) -> User | None:
    user = office_store.users.get(user_id_for_email(email))
    if user is None or not check_password_hash(user.password_hash, password): return None
    return user


def sign_in(user: User) -> None:
    session.clear()
    session["user_id"] = user.user_id
    session["business_id"] = user.business_id


def current_user() -> User | None:
    uid = session.get("user_id")
    bid = session.get("business_id")
    if not uid or not bid: return None
    return office_store.users.get(str(uid), str(bid))


def current_business_id() -> str:
    return str(session.get("business_id") or fallback_business_id)


def complete_onboarding(user: User, *, business_name: str, currency: str) -> tuple[User | None, tuple[str, ...]]:
    name = business_name.strip()
    code = currency.strip().upper()
    errors: list[str] = []
    if not name: errors.append("Business name is required.")
    if len(code) != 3 or not code.isalpha(): errors.append("Currency must be a three-letter code such as CAD.")
    if errors: return None, tuple(errors)
    office_store.businesses.save(Business(business_id=user.business_id, name=name, reporting_currency=code))
    updated = replace(user, onboarding_complete=True)
    office_store.users.save(updated)
    return updated, ()


def configure_specialist_auth(app: Flask) -> None:
    """Protect a mounted specialist when GBO_AUTH_REQUIRED is enabled."""
    app.secret_key = os.environ.get("GBO_SECRET", "gbo-dev-secret")
    app.config["SESSION_COOKIE_NAME"] = "gbo_session"

    @app.before_request
    def _require_office_account():
        if app.config.get("TESTING") or not app.config.get("GBO_AUTH_REQUIRED", False): return None
        user = current_user()
        if user is None: return redirect("/login?next=" + request.path)
        if not user.onboarding_complete: return redirect("/onboarding")
        return None
