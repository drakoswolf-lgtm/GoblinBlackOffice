"""One namespaced brand component shared by the independently mounted apps."""

from pathlib import Path

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader


def configure_branding(app: Flask) -> None:
    shared = Path(__file__).parent / "templates" / "branding"
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        PrefixLoader({"gbo": FileSystemLoader(str(shared))}),
    ])
