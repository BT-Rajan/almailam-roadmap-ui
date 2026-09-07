"""Admin-defined, reusable, informational-only document reference list
per Design/Permit/Supervision catalog activity (migration 0073) -- "we
might be using a single document for more than one activity, we can
reuse that document." Nothing here is enforced against task or
activity closure ("user manually manages it"); DocumentRequirement/
DocumentRequirementLink only exist to surface a reference checklist on
a project's tabs."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.document_requirement import DocumentRequirement, DocumentRequirementLink
from app.services import audit_service, permit_catalog_service, service_catalog_service

ENTITY_TYPE = "DOCUMENT_REQUIREMENT"


def _requirements_query(db: Session):
    return db.query(DocumentRequirement).filter(DocumentRequirement.deleted_at.is_(None))


def list_requirements(db: Session) -> list[DocumentRequirement]:
    return _requirements_query(db).order_by(DocumentRequirement.name.asc()).all()


def parse_requirement_id(raw: str) -> int:
    if not raw.isdigit():
        raise ValidationAppError("Invalid document requirement id.")
    return int(raw)


def get_requirement(db: Session, raw_id: str) -> DocumentRequirement:
    requirement = _requirements_query(db).filter(DocumentRequirement.id == parse_requirement_id(raw_id)).first()
    if requirement is None:
        raise NotFoundError("Document requirement")
    return requirement


def _assert_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    query = db.query(DocumentRequirement).filter(
        DocumentRequirement.deleted_at.is_(None), func.lower(DocumentRequirement.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        query = query.filter(DocumentRequirement.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(f'A document requirement named "{name.strip()}" already exists.')


def create_requirement(db: Session, name: str, description: str | None, user_id: int) -> DocumentRequirement:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Document requirement name is required.")
    _assert_name_available(db, clean_name)
    requirement = DocumentRequirement(name=clean_name, description=(description or "").strip() or None)
    db.add(requirement)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, requirement.id, "Document requirement added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(requirement)
    return requirement


def update_requirement(
    db: Session, raw_id: str, name: str | None, description: str | None, user_id: int
) -> DocumentRequirement:
    requirement = get_requirement(db, raw_id)
    previous_name = requirement.name
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationAppError("Document requirement name is required.")
        _assert_name_available(db, clean_name, exclude_id=requirement.id)
        requirement.name = clean_name
    if description is not None:
        requirement.description = description.strip() or None
    audit_service.log_event(
        db, ENTITY_TYPE, requirement.id, "Document requirement updated", user_id,
        previous_value=previous_name, new_value=requirement.name,
    )
    db.commit()
    db.refresh(requirement)
    return requirement


def remove_requirement(db: Session, raw_id: str, user_id: int) -> None:
    requirement = get_requirement(db, raw_id)
    removed_name = requirement.name
    requirement.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, requirement.id, "Document requirement removed", user_id, previous_value=removed_name)
    db.commit()


def _resolve_target_catalog_id(db: Session, target_type: str, raw_id: str) -> int:
    """Resolves a target's display id ("ACT-004"/"PER-003") against
    whichever catalog target_type names -- Permit uses
    permit_catalog_items, Design/Supervision both use
    service_catalog_activities (the branch isn't re-checked here,
    unlike PermitPrerequisite/SupervisionPrerequisite, since a document
    requirement's usefulness doesn't depend on which branch its target
    activity is in)."""
    if target_type == "Permit":
        return permit_catalog_service.get_permit(db, raw_id).id
    return service_catalog_service.get_activity(db, raw_id).id


def list_links_for_target(db: Session, target_type: str, target_raw_id: str) -> list[DocumentRequirementLink]:
    catalog_id = _resolve_target_catalog_id(db, target_type, target_raw_id)
    return (
        db.query(DocumentRequirementLink)
        .filter(DocumentRequirementLink.target_type == target_type, DocumentRequirementLink.target_catalog_id == catalog_id)
        .all()
    )


def list_links_for_requirement(db: Session, requirement_raw_id: str) -> list[DocumentRequirementLink]:
    requirement = get_requirement(db, requirement_raw_id)
    return (
        db.query(DocumentRequirementLink)
        .filter(DocumentRequirementLink.document_requirement_id == requirement.id)
        .all()
    )


def add_link(db: Session, requirement_raw_id: str, target_type: str, target_raw_id: str) -> DocumentRequirementLink:
    requirement = get_requirement(db, requirement_raw_id)
    catalog_id = _resolve_target_catalog_id(db, target_type, target_raw_id)
    existing = (
        db.query(DocumentRequirementLink)
        .filter(
            DocumentRequirementLink.document_requirement_id == requirement.id,
            DocumentRequirementLink.target_type == target_type,
            DocumentRequirementLink.target_catalog_id == catalog_id,
        )
        .first()
    )
    if existing is not None:
        return existing
    link = DocumentRequirementLink(
        document_requirement_id=requirement.id, target_type=target_type, target_catalog_id=catalog_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_link(db: Session, link_id: int) -> None:
    link = db.query(DocumentRequirementLink).filter(DocumentRequirementLink.id == link_id).first()
    if link is None:
        raise NotFoundError("Document requirement link")
    db.delete(link)
    db.commit()
