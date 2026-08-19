from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.service_catalog import ServiceCatalogActivity, ServiceCatalogItem
from app.services import audit_service

ENTITY_TYPE = "SERVICE_CATALOG_ITEM"

# The services this app used to ship as a hardcoded, uneditable list
# (PROJECT_SERVICES in the frontend). Seeded once so the admin catalog
# page -- and the project-creation Service dropdown that now reads from
# it -- isn't stuck on an empty state on a fresh install, same reasoning
# as workflow_service._ensure_seeded.
DEFAULT_SERVICE_NAMES = [
    "Structural Engineering",
    "MEP Design",
    "Architectural Design",
    "Fire & Safety Engineering",
    "Civil Engineering",
]


def _ensure_seeded(db: Session) -> None:
    if db.query(ServiceCatalogItem).filter(ServiceCatalogItem.deleted_at.is_(None)).first() is not None:
        return
    for name in DEFAULT_SERVICE_NAMES:
        db.add(ServiceCatalogItem(name=name))
    db.commit()


def _services_query(db: Session):
    return (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.deleted_at.is_(None))
        .options(joinedload(ServiceCatalogItem.activities))
    )


def list_services(db: Session) -> list[ServiceCatalogItem]:
    _ensure_seeded(db)
    return _services_query(db).order_by(ServiceCatalogItem.name.asc()).all()


def parse_service_id(raw: str) -> int:
    text = raw.removeprefix("SVC-") if raw.upper().startswith("SVC-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid service id.")
    return int(text)


def parse_activity_id(raw: str) -> int:
    text = raw.removeprefix("ACT-") if raw.upper().startswith("ACT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid activity id.")
    return int(text)


def get_service(db: Session, raw_id: str) -> ServiceCatalogItem:
    service = (
        _services_query(db)
        .filter(ServiceCatalogItem.id == parse_service_id(raw_id))
        .first()
    )
    if not service:
        raise NotFoundError("Service")
    return service


def get_activity(db: Session, raw_id: str) -> ServiceCatalogActivity:
    activity = db.query(ServiceCatalogActivity).filter(ServiceCatalogActivity.id == parse_activity_id(raw_id)).first()
    if not activity:
        raise NotFoundError("Activity")
    return activity


def _assert_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    # Case-insensitive: "MEP Design" and "mep design" are the same
    # service to an admin typing it into the list, even though MySQL's
    # default collation would already treat these VARCHAR columns as
    # case-insensitive -- this makes that intent explicit rather than
    # relying on the column collation.
    query = db.query(ServiceCatalogItem).filter(
        ServiceCatalogItem.deleted_at.is_(None),
        func.lower(ServiceCatalogItem.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        query = query.filter(ServiceCatalogItem.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(f'A service named "{name.strip()}" already exists.')


def create_service(db: Session, name: str, user_id: int) -> ServiceCatalogItem:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Service name is required.")
    _assert_name_available(db, clean_name)
    service = ServiceCatalogItem(name=clean_name)
    db.add(service)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, service.id, "Service added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(service)
    return service


def rename_service(db: Session, service_raw_id: str, name: str, user_id: int) -> ServiceCatalogItem:
    service = get_service(db, service_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Service name is required.")
    _assert_name_available(db, clean_name, exclude_id=service.id)
    previous_name = service.name
    service.name = clean_name
    audit_service.log_event(
        db, ENTITY_TYPE, service.id, "Service renamed", user_id, previous_value=previous_name, new_value=clean_name,
    )
    db.commit()
    db.refresh(service)
    return service


def remove_service(db: Session, service_raw_id: str, user_id: int) -> None:
    # Soft-delete, same convention as every other admin-configurable
    # entity in this codebase (clients, projects, government forms) --
    # a hard delete plus a DB-level unique constraint on name would
    # permanently block re-adding the same service name later, which is
    # exactly the scenario soft-delete exists to avoid. The child
    # activities are left as-is; they're only ever reachable through
    # get_service (which filters deleted_at IS NULL), so they simply
    # stop being visible once the parent service is removed.
    service = get_service(db, service_raw_id)
    removed_name = service.name
    service.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, service.id, "Service removed", user_id, previous_value=removed_name)
    db.commit()


def add_activity(db: Session, service_raw_id: str, name: str, fixed_cost, user_id: int) -> ServiceCatalogActivity:
    service = get_service(db, service_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Activity name is required.")
    activity = ServiceCatalogActivity(service_id=service.id, name=clean_name, fixed_cost=fixed_cost)
    db.add(activity)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, service.id, "Activity added", user_id, new_value=f"{clean_name} ({fixed_cost})",
    )
    db.commit()
    db.refresh(activity)
    return activity


def update_activity(
    db: Session, activity_raw_id: str, name: str | None, fixed_cost, user_id: int,
) -> ServiceCatalogActivity:
    activity = get_activity(db, activity_raw_id)
    previous_name = activity.name
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationAppError("Activity name is required.")
        activity.name = clean_name
    if fixed_cost is not None:
        activity.fixed_cost = fixed_cost
    audit_service.log_event(
        db, ENTITY_TYPE, activity.service_id, "Activity updated", user_id,
        previous_value=previous_name, new_value=activity.name,
    )
    db.commit()
    db.refresh(activity)
    return activity


def remove_activity(db: Session, activity_raw_id: str, user_id: int) -> None:
    activity = get_activity(db, activity_raw_id)
    service_id = activity.service_id
    removed_name = activity.name
    db.delete(activity)
    audit_service.log_event(db, ENTITY_TYPE, service_id, "Activity removed", user_id, previous_value=removed_name)
    db.commit()
