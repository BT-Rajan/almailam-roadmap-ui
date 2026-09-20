from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.government import GovernmentAuthority, GovernmentForm
from app.models.permit_catalog import PermitCatalogItem
from app.services import audit_service, government_service

ENTITY_TYPE = "PERMIT_CATALOG_ITEM"


def _permits_query(db: Session):
    return db.query(PermitCatalogItem).filter(PermitCatalogItem.deleted_at.is_(None))


def list_permits(db: Session) -> list[PermitCatalogItem]:
    return _permits_query(db).order_by(PermitCatalogItem.name.asc()).all()


def parse_permit_id(raw: str) -> int:
    text = raw.removeprefix("PER-") if raw.upper().startswith("PER-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid permit id.")
    return int(text)


def get_permit(db: Session, raw_id: str) -> PermitCatalogItem:
    permit = _permits_query(db).filter(PermitCatalogItem.id == parse_permit_id(raw_id)).first()
    if not permit:
        raise NotFoundError("Permit")
    return permit


def _assert_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    # Case-insensitive, same rationale as service_catalog_service: "Building
    # Permit" and "building permit" are the same catalog entry to an admin
    # typing it into the list.
    query = db.query(PermitCatalogItem).filter(
        PermitCatalogItem.deleted_at.is_(None),
        func.lower(PermitCatalogItem.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        query = query.filter(PermitCatalogItem.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(f'A permit named "{name.strip()}" already exists.')


def create_permit(db: Session, name: str, fixed_cost: float, user_id: int) -> PermitCatalogItem:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Permit name is required.")
    _assert_name_available(db, clean_name)
    permit = PermitCatalogItem(name=clean_name, fixed_cost=fixed_cost)
    db.add(permit)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, permit.id, "Permit added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(permit)
    return permit


def rename_permit(db: Session, permit_raw_id: str, name: str, fixed_cost: float, user_id: int) -> PermitCatalogItem:
    permit = get_permit(db, permit_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Permit name is required.")
    _assert_name_available(db, clean_name, exclude_id=permit.id)
    previous_name = permit.name
    permit.name = clean_name
    permit.fixed_cost = fixed_cost
    audit_service.log_event(
        db, ENTITY_TYPE, permit.id, "Permit renamed", user_id, previous_value=previous_name, new_value=clean_name,
    )
    db.commit()
    db.refresh(permit)
    return permit


def remove_permit(db: Session, permit_raw_id: str, user_id: int) -> None:
    # Soft-delete, same convention as service_catalog_service -- a hard
    # delete plus a DB-level unique name constraint would permanently
    # block re-adding the same permit name later.
    permit = get_permit(db, permit_raw_id)
    removed_name = permit.name
    permit.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, permit.id, "Permit removed", user_id, previous_value=removed_name)
    db.commit()


def _clean_document_names(names: list[str] | None) -> list[str] | None:
    """Trimmed, blank-free, case-insensitively de-duplicated (first
    spelling wins, order kept). None when nothing is left -- i.e. "use
    the form's own list"."""
    seen: set[str] = set()
    cleaned: list[str] = []
    for name in names or []:
        text = name.strip()
        if text and text.lower() not in seen:
            seen.add(text.lower())
            cleaned.append(text)
    return cleaned or None


def set_application_setup(
    db: Session,
    permit_raw_id: str,
    authority_raw_id: str | None,
    form_raw_id: str | None,
    required_documents: list[str] | None,
    user_id: int,
) -> PermitCatalogItem:
    """Configures which authority and form a permit type's applications
    use, plus an optional required-documents checklist that replaces the
    form's own. Authority and form are set together or cleared together;
    the form must be an active one belonging to that authority, so a
    mismatched pair can't be saved."""
    permit = get_permit(db, permit_raw_id)
    if bool(authority_raw_id) != bool(form_raw_id):
        raise ValidationAppError("Choose both an authority and a form, or neither.")

    if authority_raw_id and form_raw_id:
        authority = government_service.get_authority(db, government_service.parse_authority_id(authority_raw_id))
        form = government_service.get_form(db, government_service.parse_form_id(form_raw_id))
        if form.authority_id != authority.id:
            raise ValidationAppError("That form belongs to a different authority.")
        if form.status != "Active":
            raise ValidationAppError("That form is archived. Choose an active form.")
        new_authority_id, new_form_id = authority.id, form.id
        new_documents = _clean_document_names(required_documents)
    else:
        # Unmapped: a checklist without a form has nothing to attach to.
        new_authority_id, new_form_id, new_documents = None, None, None

    permit.authority_id = new_authority_id
    permit.form_id = new_form_id
    permit.required_documents = new_documents
    audit_service.log_event(
        db, ENTITY_TYPE, permit.id, "Permit application setup changed", user_id,
        new_value=f"form={new_form_id}" if new_form_id else "unmapped",
    )
    db.commit()
    db.refresh(permit)
    return permit


def valid_setup_ids(db: Session) -> tuple[set[int], set[int]]:
    """Ids of authorities and forms a permit type can still use (not
    deleted, form not archived) -- a soft-deleted or archived target
    reads as \"not configured\" rather than pointing at something staff
    can no longer file against."""
    authority_ids = {
        row.id for row in db.query(GovernmentAuthority.id).filter(GovernmentAuthority.deleted_at.is_(None)).all()
    }
    form_ids = {
        row.id
        for row in db.query(GovernmentForm.id)
        .filter(GovernmentForm.deleted_at.is_(None), GovernmentForm.status == "Active")
        .all()
    }
    return authority_ids, form_ids


def resolve_application_setup(
    db: Session, catalog_item_id: int | None
) -> tuple[GovernmentAuthority, GovernmentForm, list[str]]:
    """The authority, form and required-documents checklist an
    application for this permit type starts with. Raises a plain,
    actionable error when the permit type hasn't been set up (or its
    form/authority was since retired)."""
    not_configured = ValidationAppError(
        "This permit type isn't set up for applications yet. Ask an administrator to choose its "
        "authority and form in Administration > Permit Catalog."
    )
    permit = (
        db.query(PermitCatalogItem)
        .filter(PermitCatalogItem.id == catalog_item_id, PermitCatalogItem.deleted_at.is_(None))
        .first()
        if catalog_item_id
        else None
    )
    if permit is None or permit.authority_id is None or permit.form_id is None:
        raise not_configured
    authority_ids, form_ids = valid_setup_ids(db)
    if permit.authority_id not in authority_ids or permit.form_id not in form_ids:
        raise not_configured
    authority = government_service.get_authority(db, permit.authority_id)
    form = government_service.get_form(db, permit.form_id)
    documents = list(permit.required_documents) if permit.required_documents else list(form.required_documents)
    return authority, form, documents
