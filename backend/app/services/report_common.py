"""Small pieces shared by the date-ranged reports."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, column, text
from sqlalchemy.orm import Session

from app.services.report_period import Period


def money(value) -> float:
    return float(Decimal(str(value or 0)).quantize(Decimal("0.01")))


def completions(db: Session, entity_type: str, period: Period | None, entity_ids: set[int] | None = None) -> dict[int, datetime]:
    """entity id -> its latest completion time (naive UTC) within the
    period (or ever, with period=None), from the audit log -- every path
    that completes a task or a project writes a row whose new_value is
    'Completed'. Callers still check the entity is Completed *now* (a
    reopened one doesn't count)."""
    sql = (
        "SELECT entity_id, MAX(changed_at) AS completed_at FROM audit_log "
        "WHERE entity_type = :entity_type AND new_value = 'Completed'"
    )
    params: dict = {"entity_type": entity_type}
    if period is not None:
        sql += " AND changed_at >= :start AND changed_at < :end"
        params.update({"start": period.utc_start, "end": period.utc_end_exclusive})
    if entity_ids is not None:
        if not entity_ids:
            return {}
        placeholders = ", ".join(f":id{i}" for i in range(len(entity_ids)))
        sql += f" AND entity_id IN ({placeholders})"
        params.update({f"id{i}": entity_id for i, entity_id in enumerate(entity_ids)})
    rows = db.execute(
        text(sql + " GROUP BY entity_id").columns(column("entity_id", Integer), column("completed_at", DateTime)),
        params,
    ).all()
    return {entity_id: completed_at for entity_id, completed_at in rows}
