"""Approvals & Permits: which government forms a project has actually
filled in and saved, organized by the form's authority (MEW/KFD/
Baladia/...) in the UI. See models.government.ProjectFormEntry's own
docstring for how this differs from GovernmentSubmission (the
authority-filing-and-decision workflow, untouched by this module).

Saving does two things in one action, matching how staff actually work
here: persists the filled-in values AND renders the same data to a PDF
saved as a Project Document -- there's no separate "save the data" step
from "generate the PDF" step. A project can only have one entry per
form (create_project_form_entry enforces this) -- filling the same form
again means editing the existing entry (update_project_form_entry), not
creating a second one.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.government import GovernmentForm, ProjectFormEntry
from app.models.project import Project
from app.services import audit_service, document_service, government_service, pdf_render, project_service

ENTITY_TYPE = "PROJECT_FORM_ENTRY"


def parse_entry_id(raw: str) -> int:
    text = raw.removeprefix("PFE-") if raw.upper().startswith("PFE-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid form entry id.")
    return int(text)


def list_project_form_entries(db: Session, project_id: int) -> list[ProjectFormEntry]:
    return (
        db.query(ProjectFormEntry)
        .filter(ProjectFormEntry.project_id == project_id)
        .order_by(ProjectFormEntry.created_at.asc())
        .all()
    )


def get_project_form_entry(db: Session, project_id: int, entry_id: int) -> ProjectFormEntry:
    entry = (
        db.query(ProjectFormEntry)
        .filter(ProjectFormEntry.id == entry_id, ProjectFormEntry.project_id == project_id)
        .first()
    )
    if entry is None:
        raise NotFoundError("Form entry")
    return entry


def _render_and_save_pdf(db: Session, project: Project, form: GovernmentForm, field_values: dict, actor_id: int):
    if not form.template:
        raise ValidationAppError("This form has no template to fill in.")
    rendered_body = pdf_render.render_template(form.template, field_values)
    pdf_bytes = pdf_render.render_agreement_pdf(form.title, rendered_body)
    return document_service.create_document_from_bytes(
        db, project, form.title, "Government Agreement", pdf_bytes, f"{form.title}.pdf", actor_id, source_form_id=form.id
    )


def create_project_form_entry(
    db: Session, project: Project, form_id: int, field_values: dict[str, str], actor_id: int | None
) -> ProjectFormEntry:
    form = government_service.get_form(db, form_id)
    existing = (
        db.query(ProjectFormEntry)
        .filter(ProjectFormEntry.project_id == project.id, ProjectFormEntry.form_id == form_id)
        .first()
    )
    if existing is not None:
        raise ValidationAppError(f"'{form.title}' has already been added to this project.")
    project_service.assert_project_open_for_new_work(project)

    document = _render_and_save_pdf(db, project, form, field_values, actor_id)
    entry = ProjectFormEntry(
        project_id=project.id, form_id=form.id, field_values=field_values, document_id=document.id, created_by=actor_id
    )
    db.add(entry)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, entry.id, f"Form filled: {form.title}", actor_id, new_value=form.title)
    db.commit()
    db.refresh(entry)
    return entry


def update_project_form_entry(
    db: Session, project: Project, entry_id: int, field_values: dict[str, str], actor_id: int | None
) -> ProjectFormEntry:
    entry = get_project_form_entry(db, project.id, entry_id)
    form = government_service.get_form(db, entry.form_id)
    document = _render_and_save_pdf(db, project, form, field_values, actor_id)
    entry.field_values = field_values
    entry.document_id = document.id
    audit_service.log_event(db, ENTITY_TYPE, entry.id, f"Form re-filled: {form.title}", actor_id)
    db.commit()
    db.refresh(entry)
    return entry


def set_project_form_entry_status(
    db: Session, project_id: int, entry_id: int, status: str, actor_id: int | None
) -> ProjectFormEntry:
    entry = get_project_form_entry(db, project_id, entry_id)
    audit_service.log_event(
        db, ENTITY_TYPE, entry.id, "Form entry status changed", actor_id,
        previous_value=entry.status, new_value=status,
    )
    entry.status = status
    db.commit()
    db.refresh(entry)
    return entry


def delete_project_form_entry(db: Session, project_id: int, entry_id: int, actor_id: int | None) -> None:
    """Removes the filed-form record, freeing this form up to be added
    to the project again -- leaves the generated PDF Document itself in
    place (still visible from the project's Documents tab) rather than
    deleting it too, same "don't cascade into unrelated data" caution
    as every other delete in this app."""
    entry = get_project_form_entry(db, project_id, entry_id)
    form = government_service.get_form(db, entry.form_id)
    audit_service.log_event(db, ENTITY_TYPE, entry.id, f"Form entry removed: {form.title}", actor_id, previous_value=form.title)
    db.delete(entry)
    db.commit()
