"""Admin CRUD for PermitPrerequisite -- "these Design activities must be
Complete before this Permit is eligible to start" (migration 0073). See
project_service._recompute_permit_eligibility for where this is
actually evaluated per-project. SupervisionPrerequisite gets its own
matching set of functions once Phase 4 needs them -- kept separate
rather than generalized into one polymorphic set, same reasoning as
the two model tables themselves (see app/models/prerequisite.py)."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.prerequisite import PermitPrerequisite
from app.services import permit_catalog_service, service_catalog_service


def list_permit_prerequisites(db: Session, permit_raw_id: str) -> list[PermitPrerequisite]:
    permit = permit_catalog_service.get_permit(db, permit_raw_id)
    return (
        db.query(PermitPrerequisite)
        .filter(PermitPrerequisite.permit_catalog_item_id == permit.id)
        .order_by(PermitPrerequisite.id.asc())
        .all()
    )


def add_permit_prerequisite(db: Session, permit_raw_id: str, design_activity_raw_id: str) -> PermitPrerequisite:
    permit = permit_catalog_service.get_permit(db, permit_raw_id)
    activity = service_catalog_service.get_activity(db, design_activity_raw_id)
    if activity.service.branch != "Design":
        raise ValidationAppError("A permit prerequisite must reference a Design activity.")
    existing = (
        db.query(PermitPrerequisite)
        .filter(
            PermitPrerequisite.permit_catalog_item_id == permit.id,
            PermitPrerequisite.design_activity_id == activity.id,
        )
        .first()
    )
    if existing is not None:
        return existing
    prerequisite = PermitPrerequisite(permit_catalog_item_id=permit.id, design_activity_id=activity.id)
    db.add(prerequisite)
    db.commit()
    db.refresh(prerequisite)
    return prerequisite


def remove_permit_prerequisite(db: Session, prerequisite_id: int) -> None:
    prerequisite = db.query(PermitPrerequisite).filter(PermitPrerequisite.id == prerequisite_id).first()
    if prerequisite is None:
        raise NotFoundError("Permit prerequisite")
    db.delete(prerequisite)
    db.commit()
