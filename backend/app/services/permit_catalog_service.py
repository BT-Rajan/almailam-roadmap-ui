from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.permit_catalog import PermitCatalogItem
from app.services import audit_service

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


def create_permit(db: Session, name: str, user_id: int) -> PermitCatalogItem:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Permit name is required.")
    _assert_name_available(db, clean_name)
    permit = PermitCatalogItem(name=clean_name)
    db.add(permit)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, permit.id, "Permit added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(permit)
    return permit


def rename_permit(db: Session, permit_raw_id: str, name: str, user_id: int) -> PermitCatalogItem:
    permit = get_permit(db, permit_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Permit name is required.")
    _assert_name_available(db, clean_name, exclude_id=permit.id)
    previous_name = permit.name
    permit.name = clean_name
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
