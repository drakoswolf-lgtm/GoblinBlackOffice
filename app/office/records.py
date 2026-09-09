"""Human-facing creation helpers for shared Office records."""
from __future__ import annotations
import uuid
from app.core.models import Client, Project
from app.core.runtime import office_store


def create_client(*, business_id: str, name: str, email: str = "", phone: str = ""):
    clean = name.strip()
    if not clean:
        return None, ("Client name is required.",)
    client = Client(
        client_id=f"CLI-{uuid.uuid4().hex[:12].upper()}",
        business_id=business_id,
        name=clean,
        email=email.strip() or None,
        phone=phone.strip() or None,
    )
    office_store.clients.save(client)
    return client, ()


def create_project(*, business_id: str, client_id: str, name: str, description: str = ""):
    clean = name.strip()
    client = office_store.clients.get(client_id, business_id)
    errors = []
    if not clean:
        errors.append("Project name is required.")
    if client is None:
        errors.append("Choose a client from this Office.")
    if errors:
        return None, tuple(errors)
    project = Project(
        project_id=f"PRJ-{uuid.uuid4().hex[:12].upper()}",
        business_id=business_id,
        client_id=client_id,
        name=clean,
        description=description.strip() or None,
    )
    office_store.projects.save(project)
    return project, ()
