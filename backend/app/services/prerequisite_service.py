"""Admin CRUD for PermitPrerequisite -- "these Design activities must be
Complete before this Permit is eligible to start" (migration 0073). See
project_service._recompute_permit_eligibility for where this is
actually evaluated per-project. SupervisionPrerequisite gets its own
matching set of functions once Phase 4 needs them -- kept separate
rather than generalized into one polymorphic set, same reasoning as
the two model tables themselves (see app/models/prerequisite.py)."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.prerequisite import PermitPrerequisite, SupervisionPrerequisite
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


def list_supervision_prerequisites(db: Session, supervision_activity_raw_id: str) -> list[SupervisionPrerequisite]:
    activity = service_catalog_service.get_activity(db, supervision_activity_raw_id)
    return (
        db.query(SupervisionPrerequisite)
        .filter(SupervisionPrerequisite.supervision_activity_id == activity.id)
        .order_by(SupervisionPrerequisite.id.asc())
        .all()
    )


def add_supervision_prerequisite(
    db: Session, supervision_activity_raw_id: str, design_activity_raw_id: str
) -> SupervisionPrerequisite:
    supervision_activity = service_catalog_service.get_activity(db, supervision_activity_raw_id)
    if supervision_activity.service.branch != "Supervision":
        raise ValidationAppError("A supervision prerequisite's target must be a Supervision activity.")
    design_activity = service_catalog_service.get_activity(db, design_activity_raw_id)
    if design_activity.service.branch != "Design":
        raise ValidationAppError("A supervision prerequisite must reference a Design activity.")
    existing = (
        db.query(SupervisionPrerequisite)
        .filter(
            SupervisionPrerequisite.supervision_activity_id == supervision_activity.id,
            SupervisionPrerequisite.design_activity_id == design_activity.id,
        )
        .first()
    )
    if existing is not None:
        return existing
    prerequisite = SupervisionPrerequisite(
        supervision_activity_id=supervision_activity.id, design_activity_id=design_activity.id,
    )
    db.add(prerequisite)
    db.commit()
    db.refresh(prerequisite)
    return prerequisite


def remove_supervision_prerequisite(db: Session, prerequisite_id: int) -> None:
    prerequisite = db.query(SupervisionPrerequisite).filter(SupervisionPrerequisite.id == prerequisite_id).first()
    if prerequisite is None:
        raise NotFoundError("Supervision prerequisite")
    db.delete(prerequisite)
    db.commit()
