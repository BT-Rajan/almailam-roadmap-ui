from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.government import GovernmentAuthority, GovernmentForm


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


def create_authority(db: Session, payload) -> GovernmentAuthority:
    authority = GovernmentAuthority(
        name=payload.name, category=payload.category, website=payload.website, description=payload.description
    )
    db.add(authority)
    db.commit()
    db.refresh(authority)
    return authority


def update_authority(db: Session, authority_id: int, payload) -> GovernmentAuthority:
    authority = get_authority(db, authority_id)
    authority.name = payload.name
    authority.category = payload.category
    authority.website = payload.website
    authority.description = payload.description
    db.commit()
    db.refresh(authority)
    return authority


def delete_authority(db: Session, authority_id: int) -> None:
    authority = get_authority(db, authority_id)
    now = datetime.now(timezone.utc)
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


def create_form(db: Session, payload) -> GovernmentForm:
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
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


def update_form(db: Session, form_id: int, payload) -> GovernmentForm:
    form = get_form(db, form_id)
    get_authority(db, parse_authority_id(payload.authorityId))
    form.authority_id = parse_authority_id(payload.authorityId)
    form.form_code = payload.formCode
    form.title = payload.title
    form.version = payload.version
    form.language = payload.language
    form.category = payload.category
    form.description = payload.description
    form.required_documents = payload.requiredDocuments
    form.preview_url = payload.previewUrl
    db.commit()
    db.refresh(form)
    return form


def delete_form(db: Session, form_id: int) -> None:
    form = get_form(db, form_id)
    form.deleted_at = datetime.now(timezone.utc)
    db.commit()


def set_form_status(db: Session, form_id: int, status: str) -> GovernmentForm:
    form = get_form(db, form_id)
    form.status = status
    db.commit()
    db.refresh(form)
    return form
