"""One namespaced brand component shared by the independently mounted apps."""

from pathlib import Path

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader
from app.office.soundtrack import soundtrack_catalogue


def configure_branding(app: Flask) -> None:
    shared = Path(__file__).parent / "templates" / "branding"
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        PrefixLoader({"gbo": FileSystemLoader(str(shared))}),
    ])

    @app.context_processor
    def office_media():
        return {"soundtrack": soundtrack_catalogue()}
