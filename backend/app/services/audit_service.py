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


def get_last_event_time(db: Session, entity_type: str, entity_id: int, event_label: str):
    """Most recent changed_at for a specific event label on an entity,
    or None if it's never happened. Used by staleness checks (see
    client_service.check_and_notify_stale_onboarding,
    project_service.check_and_notify_stale_projects's sibling
    timeline_service.get_last_stage_event) that need "how long has this
    genuinely sat since it last moved," not just when the record itself
    was created."""
    row = db.execute(
        text(
            "SELECT changed_at FROM audit_log "
            "WHERE entity_type = :entity_type AND entity_id = :entity_id AND event_label = :event_label "
            "ORDER BY changed_at DESC LIMIT 1"
        ),
        {"entity_type": entity_type, "entity_id": entity_id, "event_label": event_label},
    ).first()
    return row[0] if row else None


def list_all(
    db: Session,
    entity_type: str | None = None,
    entity_id: int | None = None,
    changed_by: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[dict], int]:
    """Global, filterable audit log listing for the Administration audit
    viewer -- distinct from get_history() above, which is scoped to one
    entity and used by every entity's own "Audit Trail" tab."""
    conditions = []
    params: dict = {}
    if entity_type:
        conditions.append("entity_type = :entity_type")
        params["entity_type"] = entity_type
    if entity_id is not None:
        conditions.append("entity_id = :entity_id")
        params["entity_id"] = entity_id
    if changed_by is not None:
        conditions.append("changed_by = :changed_by")
        params["changed_by"] = changed_by
    if start_date:
        conditions.append("changed_at >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("changed_at <= :end_date")
        params["end_date"] = end_date
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    total = db.execute(text(f"SELECT COUNT(*) FROM audit_log {where}"), params).scalar() or 0

    page = max(page, 1)
    page_size = max(min(page_size, 200), 1)
    offset = (page - 1) * page_size
    result = db.execute(
        text(
            "SELECT id, entity_type, entity_id, event_label, previous_value, new_value, "
            f"reason, changed_by, changed_at FROM audit_log {where} "
            "ORDER BY changed_at DESC, id DESC LIMIT :limit OFFSET :offset"
        ),
        {**params, "limit": page_size, "offset": offset},
    )
    rows = [dict(row._mapping) for row in result]

    user_ids = {row["changed_by"] for row in rows if row["changed_by"] is not None}
    names: dict[int, str] = {}
    if user_ids:
        from app.models.user import User

        for user_id, full_name in db.query(User.id, User.full_name).filter(User.id.in_(user_ids)).all():
            names[user_id] = full_name

    for row in rows:
        row["user"] = names.get(row.pop("changed_by"), "System")

    return rows, total


def get_history(db: Session, entity_type: str, entity_id: int) -> list[dict]:
    """Every history endpoint (clients, projects, quotations, contracts,
    tasks, documents, government submissions, financial agreements) calls
    this one function, so resolving changed_by to a display name here (in
    bulk, one query) benefits all of them rather than each endpoint doing
    its own per-row lookup.

    Returns already-camelCase, JSON-ready dicts -- none of the eight
    audit-events endpoints that call this apply a response_model, so
    whatever shape comes out of here is exactly what reaches the
    frontend. It was previously the raw SQL column names (event_label,
    changed_at, previous_value, new_value), which don't match any
    frontend type's fields (action, timestamp, previousValue, newValue) --
    the label and reason came through fine (same key name, `reason`, and
    `user` was already resolved to a name above), but the activity
    description and the timestamp were both silently undefined on every
    audit trail in the app that's actually wired up to a screen.
    """
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

    return [
        {
            "id": str(row["id"]),
            "action": row["event_label"],
            "user": names.get(row["changed_by"], "System"),
            "timestamp": row["changed_at"].isoformat() if row["changed_at"] else None,
            "previousValue": row["previous_value"],
            "newValue": row["new_value"],
            "reason": row["reason"],
        }
        for row in rows
    ]
