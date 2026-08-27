from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.government import GovernmentAuthority, GovernmentForm
from app.services import audit_service, document_service, pdf_render, project_service

AUTHORITY_ENTITY_TYPE = "GOVERNMENT_AUTHORITY"
FORM_ENTITY_TYPE = "GOVERNMENT_FORM"


def _parse_id(raw: str, prefix: str) -> int:
    text = raw.removeprefix(f"{prefix}-") if raw.upper().startswith(f"{prefix}-") else raw
    if not text.isdigit():
        raise ValidationAppError(f"Invalid {prefix.lower()} id.")
    return int(text)


def parse_authority_id(raw: str) -> int:
    return _parse_id(raw, "AUTH")


def parse_form_id(raw: str) -> int:
    return _parse_id(raw, "FORM")


# --- authorities -----------------------------------------------------------


def list_authorities(db: Session) -> list[GovernmentAuthority]:
    return (
        db.query(GovernmentAuthority)
        .filter(GovernmentAuthority.deleted_at.is_(None))
        .order_by(GovernmentAuthority.id.asc())
        .all()
    )


def get_authority(db: Session, authority_id: int) -> GovernmentAuthority:
    authority = (
        db.query(GovernmentAuthority)
        .filter(GovernmentAuthority.id == authority_id, GovernmentAuthority.deleted_at.is_(None))
        .first()
    )
    if authority is None:
        raise NotFoundError("Authority")
    return authority


def create_authority(db: Session, payload, actor_id: int) -> GovernmentAuthority:
    authority = GovernmentAuthority(
        name=payload.name, category=payload.category, website=payload.website, description=payload.description
    )
    db.add(authority)
    db.flush()
    audit_service.log_event(
        db, AUTHORITY_ENTITY_TYPE, authority.id, "Authority created", actor_id, new_value=authority.name
    )
    db.commit()
    db.refresh(authority)
    return authority


def update_authority(db: Session, authority_id: int, payload, actor_id: int) -> GovernmentAuthority:
    authority = get_authority(db, authority_id)
    audit_service.log_event(
        db, AUTHORITY_ENTITY_TYPE, authority.id, "Authority updated", actor_id,
        previous_value=authority.name, new_value=payload.name,
    )
    authority.name = payload.name
    authority.category = payload.category
    authority.website = payload.website
    authority.description = payload.description
    db.commit()
    db.refresh(authority)
    return authority


def delete_authority(db: Session, authority_id: int, actor_id: int) -> None:
    authority = get_authority(db, authority_id)
    now = datetime.now(timezone.utc)
    audit_service.log_event(
        db, AUTHORITY_ENTITY_TYPE, authority.id, "Authority deleted", actor_id, previous_value=authority.name
    )
    authority.deleted_at = now
    # Mirrors src/services/governmentFormService.ts's deleteAuthority, which
    # removes every form belonging to the authority alongside it -- soft
    # deletion here instead of the mock's hard delete, consistent with the
    # rest of this backend.
    db.query(GovernmentForm).filter(
        GovernmentForm.authority_id == authority_id, GovernmentForm.deleted_at.is_(None)
    ).update({"deleted_at": now})
    db.commit()


# --- forms -------------------------------------------------------------


def list_forms(db: Session, authority_id: int | None = None, status: str | None = None) -> list[GovernmentForm]:
    query = db.query(GovernmentForm).filter(GovernmentForm.deleted_at.is_(None))
    if authority_id is not None:
        query = query.filter(GovernmentForm.authority_id == authority_id)
    if status is not None:
        query = query.filter(GovernmentForm.status == status)
    return query.order_by(GovernmentForm.id.asc()).all()


def get_form(db: Session, form_id: int) -> GovernmentForm:
    form = (
        db.query(GovernmentForm)
        .filter(GovernmentForm.id == form_id, GovernmentForm.deleted_at.is_(None))
        .first()
    )
    if form is None:
        raise NotFoundError("Form")
    return form


def create_form(db: Session, payload, actor_id: int) -> GovernmentForm:
    get_authority(db, parse_authority_id(payload.authorityId))
    form = GovernmentForm(
        authority_id=parse_authority_id(payload.authorityId),
        form_code=payload.formCode,
        title=payload.title,
        version=payload.version,
        language=payload.language,
        category=payload.category,
        description=payload.description,
        required_documents=payload.requiredDocuments,
        preview_url=payload.previewUrl,
        template=payload.template,
        service_tags=payload.serviceTags,
        fields=[f.model_dump() for f in payload.fields],
    )
    db.add(form)
    db.flush()
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Form created", actor_id, new_value=form.title
    )
    db.commit()
    db.refresh(form)
    return form


def update_form(db: Session, form_id: int, payload, actor_id: int) -> GovernmentForm:
    form = get_form(db, form_id)
    get_authority(db, parse_authority_id(payload.authorityId))
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Form updated", actor_id,
        previous_value=form.title, new_value=payload.title,
    )
    form.authority_id = parse_authority_id(payload.authorityId)
    form.form_code = payload.formCode
    form.title = payload.title
    form.version = payload.version
    form.language = payload.language
    form.category = payload.category
    form.description = payload.description
    form.required_documents = payload.requiredDocuments
    form.preview_url = payload.previewUrl
    form.template = payload.template
    form.service_tags = payload.serviceTags
    form.fields = [f.model_dump() for f in payload.fields]
    db.commit()
    db.refresh(form)
    return form


def upload_sample_file(db: Session, form_id: int, file, actor_id: int) -> GovernmentForm:
    """Attaches an uploaded reference copy of the real government form
    (e.g. the blank official PDF) to check the template/fields against
    -- not parsed, purely a reference. Re-uploading replaces which file
    this form points to; the previous file is left on disk rather than
    deleted, same as every other single-file "Replace" flow in this app
    (see e.g. approval_process_service.upload_stage_gate_document)."""
    from app.core.file_storage import save_upload

    form = get_form(db, form_id)
    storage_key, original_filename, size_bytes = save_upload(file, "government-form-samples")
    form.sample_file_storage_key = storage_key
    form.sample_file_original_filename = original_filename
    form.sample_file_size_bytes = size_bytes
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Sample file uploaded", actor_id, new_value=original_filename
    )
    db.commit()
    db.refresh(form)
    return form


def delete_form(db: Session, form_id: int, actor_id: int) -> None:
    form = get_form(db, form_id)
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Form deleted", actor_id, previous_value=form.title
    )
    form.deleted_at = datetime.now(timezone.utc)
    db.commit()


def fill_form(db: Session, form_id: int, payload, actor_id: int):
    """Merges a form's {{token}} template with the given context, renders
    it to a PDF (see pdf_render), and saves it as a Project Document
    (type "Government Agreement") -- the real, DB-backed counterpart to
    the client-side-only FormTemplatePreviewDialog.vue preview."""
    form = get_form(db, form_id)
    if not form.template:
        raise ValidationAppError("This form has no template to fill in.")

    project = project_service.get_project(db, payload.projectId)
    project_service.assert_project_open_for_new_work(project)

    rendered_body = pdf_render.render_template(form.template, payload.context)
    title = (payload.title or form.title).strip() or form.title
    pdf_bytes = pdf_render.render_agreement_pdf(title, rendered_body)

    document = document_service.create_document_from_bytes(
        db, project, title, "Government Agreement", pdf_bytes, f"{title}.pdf", actor_id, source_form_id=form.id
    )
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Form filled and saved as a document", actor_id, new_value=title
    )
    db.commit()
    return document


def render_pdf(db: Session, form_id: int, payload) -> tuple[bytes, str]:
    """Renders a form's {{token}} template with the given context straight
    to PDF bytes -- nothing persisted, no project needed. The admin-facing
    counterpart to fill_form above: trying out a template (Administration
    > Government Forms) before it's ever used on a real project, where
    the point is a downloadable file, not a saved Document. Returns the
    bytes plus the title used, so the caller can name the download."""
    form = get_form(db, form_id)
    if not form.template:
        raise ValidationAppError("This form has no template to fill in.")

    rendered_body = pdf_render.render_template(form.template, payload.context)
    title = (payload.title or form.title).strip() or form.title
    pdf_bytes = pdf_render.render_agreement_pdf(title, rendered_body)
    return pdf_bytes, title


def set_form_status(db: Session, form_id: int, status: str, actor_id: int) -> GovernmentForm:
    form = get_form(db, form_id)
    audit_service.log_event(
        db, FORM_ENTITY_TYPE, form.id, "Status changed", actor_id,
        previous_value=form.status, new_value=status,
    )
    form.status = status
    db.commit()
    db.refresh(form)
    return form
