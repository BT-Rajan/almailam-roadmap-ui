from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.type_activity_catalog import TypeActivityCategory, TypeActivityItem
from app.services import audit_service

ENTITY_TYPE = "TYPE_ACTIVITY_CATEGORY"

# Seeded once so the admin catalog page -- and the New Project wizard's
# final-step activity picker that reads from it -- isn't stuck on an
# empty state on a fresh install. These are deliberately generic
# starting points; admins are expected to tailor them (see
# DEFAULT_SERVICE_NAMES in service_catalog_service.py for the identical
# pattern on the services side).
DEFAULT_CATEGORIES: dict[str, list[tuple[str, float]]] = {
    "Design": [
        ("Site Inspection", 150),
        ("Concept Drawings", 300),
        ("Structural Calculations", 400),
        ("Coordination with Authorities", 200),
    ],
    "Supervision": [
        ("Weekly Site Visits", 250),
        ("Progress Reporting", 100),
        ("Materials Testing Coordination", 150),
        ("Snagging & Handover Inspection", 200),
    ],
}


def _ensure_seeded(db: Session) -> None:
    if db.query(TypeActivityCategory).filter(TypeActivityCategory.deleted_at.is_(None)).first() is not None:
        return
    # Same check-then-insert race as service_catalog_service._ensure_seeded
    # -- acceptable here for the same reason: a lost race just means the
    # concurrent request's seed rows silently don't get inserted, not a
    # visible error, and the categories/activities end up seeded either way.
    try:
        for category_name, activities in DEFAULT_CATEGORIES.items():
            category = TypeActivityCategory(name=category_name)
            db.add(category)
            db.flush()
            for activity_name, cost in activities:
                db.add(TypeActivityItem(category_id=category.id, name=activity_name, cost=cost))
        db.commit()
    except IntegrityError:
        db.rollback()


def _categories_query(db: Session):
    return (
        db.query(TypeActivityCategory)
        .filter(TypeActivityCategory.deleted_at.is_(None))
        .options(joinedload(TypeActivityCategory.activities))
    )


def list_categories(db: Session) -> list[TypeActivityCategory]:
    _ensure_seeded(db)
    return _categories_query(db).order_by(TypeActivityCategory.name.asc()).all()


def parse_category_id(raw: str) -> int:
    text = raw.removeprefix("TAC-") if raw.upper().startswith("TAC-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid category id.")
    return int(text)


def parse_item_id(raw: str) -> int:
    text = raw.removeprefix("TAI-") if raw.upper().startswith("TAI-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid activity id.")
    return int(text)


def get_category(db: Session, raw_id: str) -> TypeActivityCategory:
    category = _categories_query(db).filter(TypeActivityCategory.id == parse_category_id(raw_id)).first()
    if not category:
        raise NotFoundError("Type activity category")
    return category


def get_item(db: Session, raw_id: str) -> TypeActivityItem:
    item = db.query(TypeActivityItem).filter(TypeActivityItem.id == parse_item_id(raw_id)).first()
    if not item:
        raise NotFoundError("Type activity")
    return item


def _assert_name_available(db: Session, name: str, exclude_id: int | None = None) -> None:
    query = db.query(TypeActivityCategory).filter(
        TypeActivityCategory.deleted_at.is_(None),
        func.lower(TypeActivityCategory.name) == name.strip().lower(),
    )
    if exclude_id is not None:
        query = query.filter(TypeActivityCategory.id != exclude_id)
    if query.first() is not None:
        raise ConflictError(f'A type category named "{name.strip()}" already exists.')


def create_category(db: Session, name: str, user_id: int) -> TypeActivityCategory:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Category name is required.")
    _assert_name_available(db, clean_name)
    category = TypeActivityCategory(name=clean_name)
    db.add(category)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, category.id, "Type category added", user_id, new_value=clean_name)
    db.commit()
    db.refresh(category)
    return category


def rename_category(db: Session, category_raw_id: str, name: str, user_id: int) -> TypeActivityCategory:
    category = get_category(db, category_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Category name is required.")
    _assert_name_available(db, clean_name, exclude_id=category.id)
    previous_name = category.name
    category.name = clean_name
    audit_service.log_event(
        db, ENTITY_TYPE, category.id, "Type category renamed", user_id,
        previous_value=previous_name, new_value=clean_name,
    )
    db.commit()
    db.refresh(category)
    return category


def remove_category(db: Session, category_raw_id: str, user_id: int) -> None:
    category = get_category(db, category_raw_id)
    removed_name = category.name
    category.deleted_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, category.id, "Type category removed", user_id, previous_value=removed_name)
    db.commit()


def add_item(db: Session, category_raw_id: str, name: str, cost, user_id: int) -> TypeActivityItem:
    category = get_category(db, category_raw_id)
    clean_name = name.strip()
    if not clean_name:
        raise ValidationAppError("Activity name is required.")
    item = TypeActivityItem(category_id=category.id, name=clean_name, cost=cost)
    db.add(item)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, category.id, "Type activity added", user_id, new_value=f"{clean_name} ({cost})",
    )
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_raw_id: str, name: str | None, cost, user_id: int) -> TypeActivityItem:
    item = get_item(db, item_raw_id)
    previous_name = item.name
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationAppError("Activity name is required.")
        item.name = clean_name
    if cost is not None:
        item.cost = cost
    audit_service.log_event(
        db, ENTITY_TYPE, item.category_id, "Type activity updated", user_id,
        previous_value=previous_name, new_value=item.name,
    )
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, item_raw_id: str, user_id: int) -> None:
    item = get_item(db, item_raw_id)
    category_id = item.category_id
    removed_name = item.name
    db.delete(item)
    audit_service.log_event(db, ENTITY_TYPE, category_id, "Type activity removed", user_id, previous_value=removed_name)
    db.commit()
