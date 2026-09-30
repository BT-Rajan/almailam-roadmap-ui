from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.catalog_names import name_key, words
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.service_catalog import ServiceCatalogActivity, ServiceCatalogItem
from app.services import audit_service

ENTITY_TYPE = "SERVICE_CATALOG_ITEM"

# The services this app used to ship as a hardcoded, uneditable list
# (PROJECT_SERVICES in the frontend). Seeded once so the admin catalog
# page -- and the project-creation Service dropdown that now reads from
# it -- isn't stuck on an empty state on a fresh install. All Design
# branch (the default) -- these are one-time fees.
DEFAULT_SERVICE_NAMES = [
    "Structural Engineering",
    "MEP Design",
    "Architectural Design",
    "Fire & Safety Engineering",
    "Civil Engineering",
]

# The single Supervision-branch service (migration 0059, replacing the
# old, separate "Additional Activity Catalog"). Its activities are
# monthly recurring fees rather than one-time -- same cost values the old
# type-activity "Supervision" category used to seed, now interpreted as
# a monthly rate instead of a flat one-time charge.
SUPERVISION_SERVICE_NAME = "Supervision"
SUPERVISION_DEFAULT_ACTIVITIES = [
    ("Weekly Site Visits", 250.00),
    ("Progress Reporting", 100.00),
    ("Materials Testing Coordination", 150.00),
    ("Snagging & Handover Inspection", 200.00),
]


def _ensure_seeded(db: Session) -> None:
    """Seeds the Design defaults and the Supervision service, each with
    its own existence check -- a single shared "any active service
    exists" guard meant that once e.g. migration 0059 inserted the lone
    Supervision row on an otherwise empty catalog, the Design defaults
    were never seeded at all.

    Each is seeded once per install: the checks count soft-deleted rows
    too, so a default an admin removes stays removed. Checking only
    active rows re-created it on the very next catalog load.

    "Permit" is no longer seeded as a Design service: permits live in the
    Permit Catalog, and a Design service can't be named "Permit" (see
    _assert_design_name_allowed)."""
    _ensure_design_defaults_seeded(db)
    _ensure_named_service_seeded(db, SUPERVISION_SERVICE_NAME, "Supervision", SUPERVISION_DEFAULT_ACTIVITIES)


def _ensure_design_defaults_seeded(db: Session) -> None:
    # Any Design row, deleted or not: an admin removing every default
    # Design service must not bring all five back.
    ever_had_design = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.branch == "Design").first() is not None
    if ever_had_design:
        return
    # Same check-then-insert race as role_service._ensure_seeded /
    # ai_config_service._ensure_seeded (see those for the fuller
    # explanation, confirmed happening on the live server for
    # role_definitions) -- now backed by a real database constraint
    # (uq_service_catalog_items_active_name, see migration 0037) rather
    # than nothing, so a concurrent duplicate attempt has something to
    # catch instead of silently inserting duplicate default services.
    try:
        for name in DEFAULT_SERVICE_NAMES:
            db.add(ServiceCatalogItem(name=name, branch="Design"))
        db.commit()
    except IntegrityError:
        db.rollback()


def _ensure_named_service_seeded(
    db: Session, name: str, branch: str, activities: list[tuple[str, float]],
) -> None:
    # Deleted rows count: once seeded, removing it is the admin's call.
    ever_existed = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.name == name).first() is not None
    if ever_existed:
        return
    try:
        service = ServiceCatalogItem(name=name, branch=branch)
        db.add(service)
        db.flush()
        for activity_name, cost in activities:
            db.add(ServiceCatalogActivity(service_id=service.id, name=activity_name, fixed_cost=cost))
        db.commit()
    except IntegrityError:
        db.rollback()


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
    # Compared by catalog_names.name_key, not just case-insensitively: an
    # exact match let "Permit" in next to "Permits". The catalog is a
    # short admin list, so comparing in Python is cheap.
    key = name_key(name)
    rows = db.query(ServiceCatalogItem.id, ServiceCatalogItem.name).filter(ServiceCatalogItem.deleted_at.is_(None))
    for row_id, row_name in rows:
        if row_id != exclude_id and name_key(row_name) == key:
            raise ConflictError(f'"{name.strip()}" is too similar to the existing service "{row_name}".')


# Permits and Supervision have their own sections in the Service Picker
# (the Permit Catalog, and the single Supervision-branch service billed
# monthly). A Design service with one of these words in its name showed
# up as a second, one-time-fee copy of them.
_DESIGN_RESERVED_WORDS = {"permit": "Permit Catalog", "supervision": "Supervision service"}


def _assert_design_name_allowed(name: str, branch: str) -> None:
    if branch != "Design":
        return
    for word in words(name):
        if word in _DESIGN_RESERVED_WORDS:
            raise ValidationAppError(
                f'"{name.strip()}" can\'t be a Design service -- add it to the '
                f"{_DESIGN_RESERVED_WORDS[word]} instead."
            )


def create_service(db: Session, name: str, branch: str, user_id: int) -> ServiceCatalogItem:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Service name is required.")
    _assert_design_name_allowed(clean_name, branch)
    _assert_name_available(db, clean_name)
    if branch == "Supervision":
        _assert_no_existing_supervision_service(db)
    service = ServiceCatalogItem(name=clean_name, branch=branch)
    db.add(service)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, service.id, "Service added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(service)
    return service


def _assert_no_existing_supervision_service(db: Session) -> None:
    """Every caller that bills Supervision work -- the project Service
    Picker (which only ever renders the *first* Supervision-branch
    service it finds), payment_service.create_agreement, and
    get_selected_supervision_activities -- assumes there's exactly one
    Supervision-branch service in the catalog (see the SUPERVISION_
    SERVICE_NAME comment above). Nothing previously stopped a second one
    from being created; it wouldn't error, it would just silently never
    appear in the picker, so any activities under it could never be
    selected on a project or billed monthly. Enforced here instead --
    add more monthly-billed activities to the existing Supervision
    service rather than creating a second one."""
    existing = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.deleted_at.is_(None), ServiceCatalogItem.branch == "Supervision")
        .first()
    )
    if existing is not None:
        raise ValidationAppError(
            f'"{existing.name}" is already the Supervision service -- only one is allowed. '
            "Add new monthly-billed activities to it instead of creating a second Supervision service."
        )


def rename_service(db: Session, service_raw_id: str, name: str, user_id: int) -> ServiceCatalogItem:
    service = get_service(db, service_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Service name is required.")
    _assert_design_name_allowed(clean_name, service.branch)
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


def _assert_cost_positive(fixed_cost) -> None:
    # Every activity is billable: a 0 KWD activity would put a free line
    # into quotations and payment plans.
    if fixed_cost is None or fixed_cost <= 0:
        raise ValidationAppError("Fixed cost must be greater than 0 KWD.")


def add_activity(db: Session, service_raw_id: str, name: str, fixed_cost, user_id: int) -> ServiceCatalogActivity:
    service = get_service(db, service_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Activity name is required.")
    _assert_cost_positive(fixed_cost)
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
        _assert_cost_positive(fixed_cost)
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
