"""jdk_clean's audit_service logs raw CRUD verbs (CREATE/UPDATE/DELETE/
RESTORE) plus one row per changed field on update. almailam's actual
history feeds (src/mock/clientAuditEvents.ts, financialAuditEvents.ts)
show one row per human-meaningful business event instead -- "Payment
Received", "Verification completed", "Adjustment Applied" -- each with
a single summarized previous/new value and an optional reason, not a
raw field-by-field diff. So the storage grain here is the event label,
not the CRUD verb; log_field_changes is kept as a convenience for the
cases that genuinely are simple field edits.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

IGNORED_FIELDS = {"created_at", "updated_at", "deleted_at"}


def log_event(
    db: Session,
    entity_type: str,
    entity_id: int,
    event_label: str,
    user_id: int | None,
    previous_value: str | None = None,
    new_value: str | None = None,
    reason: str | None = None,
) -> None:
    db.execute(
        text(
            "INSERT INTO audit_log "
            "(entity_type, entity_id, event_label, previous_value, new_value, reason, changed_by) "
            "VALUES (:entity_type, :entity_id, :event_label, :previous_value, :new_value, :reason, :user_id)"
        ),
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_label": event_label,
            "previous_value": previous_value,
            "new_value": new_value,
            "reason": reason,
            "user_id": user_id,
        },
    )


def log_field_changes(
    db: Session,
    entity_type: str,
    entity_id: int,
    changes: dict[str, tuple],
    user_id: int | None,
    label_prefix: str = "Updated",
) -> None:
    """changes: {field_name: (old_value, new_value)} -- only fields that
    actually changed. Writes one row per field, e.g. label "Updated role"."""
    for field, (old, new) in changes.items():
        if field in IGNORED_FIELDS or old == new:
            continue
        log_event(
            db,
            entity_type,
            entity_id,
            f"{label_prefix} {field.replace('_', ' ')}",
            user_id,
            previous_value=str(old) if old is not None else None,
            new_value=str(new) if new is not None else None,
        )


def get_history(db: Session, entity_type: str, entity_id: int) -> list[dict]:
    """Every future history endpoint calls this one function, so
    resolving changed_by to a display name here (in bulk, one query)
    benefits all of them rather than each endpoint doing its own
    per-row lookup."""
    result = db.execute(
        text(
            "SELECT id, event_label, previous_value, new_value, reason, changed_by, changed_at "
            "FROM audit_log WHERE entity_type = :entity_type AND entity_id = :entity_id "
            "ORDER BY changed_at DESC, id DESC"
        ),
        {"entity_type": entity_type, "entity_id": entity_id},
    )
    rows = [dict(row._mapping) for row in result]

    user_ids = {row["changed_by"] for row in rows if row["changed_by"] is not None}
    names: dict[int, str] = {}
    if user_ids:
        # Local import: audit_service will end up imported by nearly
        # every other service, so importing User at module level here
        # would risk a circular import depending on load order.
        from app.models.user import User

        for user_id, full_name in (
            db.query(User.id, User.full_name).filter(User.id.in_(user_ids)).all()
        ):
            names[user_id] = full_name

    for row in rows:
        row["user"] = names.get(row.pop("changed_by"), "System")

    return rows
