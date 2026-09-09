"""Æterna-led Black Office application shell.

This composes specialist Flask applications without forcing an immediate
rewrite of their existing routes. Ledgergut remains independently runnable and
is mounted under /ledgergut in the shared Office surface.
"""

from __future__ import annotations

from flask import Flask, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from app.ledgergut.web import app as ledgergut_app


office_app = Flask(__name__, template_folder="templates")


@office_app.route("/")
def index():
    specialists = [
        {
            "name": "Ledgergut",
            "role": "Receipts & expenses",
            "status": "live",
            "href": "/ledgergut/",
            "note": "Feed me the receipt. Keep your fingers.",
        },
        {
            "name": "SigNor",
            "role": "Agreements & scope",
            "status": "next",
            "href": None,
            "note": "Words matter. Especially the ones someone forgot to define.",
        },
        {
            "name": "Squarmish",
            "role": "Invoices & receivables",
            "status": "next",
            "href": None,
            "note": "Completed work is lovely. Paid work is lovelier.",
        },
    ]
    return render_template("office/index.html", specialists=specialists)


@office_app.route("/health")
def health():
    return {"status": "ok", "service": "goblin-black-office"}


application = DispatcherMiddleware(
    office_app,
    {
        "/ledgergut": ledgergut_app,
    },
)
