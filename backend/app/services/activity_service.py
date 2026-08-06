from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

# The entity types that make sense as "team activity" for this admin view
# -- deliberately excludes purely-system-configuration entities (company
# settings, AI configuration) that aren't really "team activity" in the
# sense this calendar is for.
ACTIVITY_ENTITY_TYPES = (
    "PROJECT",
    "CLIENT",
    "QUOTATION",
    "CONTRACT",
    "DOCUMENT",
    "TASK",
    "FINANCIAL_AGREEMENT",
    "WORKFLOW_TEMPLATE",
)

ENTITY_TYPE_TO_FRONTEND = {
    "PROJECT": "project",
    "CLIENT": "client",
    "QUOTATION": "quotation",
    "CONTRACT": "contract",
    "DOCUMENT": "document",
    "TASK": "task",
    "FINANCIAL_AGREEMENT": "payment",
    "WORKFLOW_TEMPLATE": "workflow",
}

ACTIVITY_TYPES = ("new", "updated", "delayed", "completed", "assigned", "commented", "approved", "rejected")


def _infer_activity_type(event_label: str) -> str:
    """audit_log stores a free-text event label (e.g. "Project created",
    "Task deleted"), not a discrete activity-type code, so this infers one
    from the label text. Note "delayed" is never inferred here -- there is
    no real "something became delayed" event logged anywhere in the app
    (it would have to be computed from overdue due dates, a different kind
    of signal than an audit event), so it's honestly left at 0 in the
    daily summaries below rather than faked from a text match that would
    just be wrong."""
    lower = event_label.lower()
    if any(word in lower for word in ("created", "onboarded", "added", "uploaded", "recorded", "submitted")):
        return "new"
    if "deleted" in lower or "removed" in lower:
        return "rejected"
    if "approved" in lower:
        return "approved"
    if "rejected" in lower:
        return "rejected"
    if "completed" in lower or "signed" in lower:
        return "completed"
    if "assigned" in lower:
        return "assigned"
    if "comment" in lower:
        return "commented"
    return "updated"


def _resolve_projects(db: Session, rows: list[dict]) -> dict[tuple[str, int], tuple[str | None, str | None]]:
    """Batched (not per-row) lookup of which project each audit row
    belongs to, keyed by (entity_type, entity_id) -> (project_no, project_name).
    Clients and workflow templates have no project association."""
    from app.models.contract import Contract
    from app.models.document import ProjectDocument
    from app.models.payment import FinancialAgreement
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.task import Task

    ids_by_type: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        ids_by_type[row["entity_type"]].add(row["entity_id"])

    result: dict[tuple[str, int], tuple[str | None, str | None]] = {}

    def _project_lookup(project_ids: set[int]) -> dict[int, tuple[str, str]]:
        if not project_ids:
            return {}
        return {
            p.id: (p.project_no, p.project_name)
            for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
        }

    if ids_by_type["PROJECT"]:
        for p in db.query(Project).filter(Project.id.in_(ids_by_type["PROJECT"])).all():
            result[("PROJECT", p.id)] = (p.project_no, p.project_name)

    for model, entity_type in (
        (Task, "TASK"),
        (ProjectDocument, "DOCUMENT"),
        (Quotation, "QUOTATION"),
        (Contract, "CONTRACT"),
        (FinancialAgreement, "FINANCIAL_AGREEMENT"),
    ):
        entity_ids = ids_by_type[entity_type]
        if not entity_ids:
            continue
        rows_for_type = db.query(model.id, model.project_id).filter(model.id.in_(entity_ids)).all()
        project_ids = {row.project_id for row in rows_for_type}
        projects = _project_lookup(project_ids)
        for row in rows_for_type:
            project = projects.get(row.project_id)
            result[(entity_type, row.id)] = project if project else (None, None)

    return result


def _fetch_rows(
    db: Session,
    start_date: str,
    end_date: str,
    project_no: str | None = None,
    changed_by: int | None = None,
    activity_type: str | None = None,
) -> list[dict]:
    placeholders = ", ".join(f"'{t}'" for t in ACTIVITY_ENTITY_TYPES)
    conditions = [
        f"entity_type IN ({placeholders})",
        "changed_at >= :start_date",
        "changed_at < :end_date",
    ]
    params: dict = {"start_date": start_date, "end_date": end_date}
    if changed_by is not None:
        conditions.append("changed_by = :changed_by")
        params["changed_by"] = changed_by

    where = " AND ".join(conditions)
    result = db.execute(
        text(
            "SELECT id, entity_type, entity_id, event_label, previous_value, new_value, "
            f"changed_by, changed_at FROM audit_log WHERE {where} ORDER BY changed_at DESC, id DESC"
        ),
        params,
    )
    rows = [dict(row._mapping) for row in result]

    from app.models.user import User

    user_ids = {row["changed_by"] for row in rows if row["changed_by"] is not None}
    names: dict[int, str] = {}
    if user_ids:
        for user_id, full_name in db.query(User.id, User.full_name).filter(User.id.in_(user_ids)).all():
            names[user_id] = full_name

    projects = _resolve_projects(db, rows)

    activities = []
    for row in rows:
        inferred_type = _infer_activity_type(row["event_label"])
        if activity_type and inferred_type != activity_type:
            continue
        project_no_val, project_name_val = projects.get((row["entity_type"], row["entity_id"]), (None, None))
        if project_no and project_no_val != project_no:
            continue
        timestamp = row["changed_at"]
        activities.append(
            {
                "id": str(row["id"]),
                "type": inferred_type,
                "entityType": ENTITY_TYPE_TO_FRONTEND.get(row["entity_type"], row["entity_type"].lower()),
                "entityId": str(row["entity_id"]),
                "entityName": row["new_value"] or row["previous_value"] or f"{row['entity_type']} #{row['entity_id']}",
                "projectId": project_no_val,
                "projectName": project_name_val,
                "userId": str(row["changed_by"]) if row["changed_by"] is not None else "",
                "userName": names.get(row["changed_by"], "System"),
                "description": row["event_label"],
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
            }
        )
    return activities


def _summarize(day: date, activities: list[dict]) -> dict:
    counts = dict.fromkeys(ACTIVITY_TYPES, 0)
    for activity in activities:
        counts[activity["type"]] += 1
    return {
        "date": day.isoformat(),
        **counts,
        "total": len(activities),
        "activities": activities,
    }


def get_day_activity(db: Session, day: date) -> dict:
    start = day.isoformat()
    end = (day + timedelta(days=1)).isoformat()
    activities = _fetch_rows(db, start, end)
    return _summarize(day, activities)


def get_month_activity(db: Session, year: int, month: int) -> list[dict]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    activities = _fetch_rows(db, start.isoformat(), end.isoformat())

    by_day: dict[str, list[dict]] = defaultdict(list)
    for activity in activities:
        day_key = activity["timestamp"][:10]
        by_day[day_key].append(activity)

    return [_summarize(date.fromisoformat(day_key), items) for day_key, items in sorted(by_day.items())]


def get_filtered_activities(
    db: Session,
    start_date: str,
    end_date: str,
    project_no: str | None = None,
    changed_by: int | None = None,
    activity_type: str | None = None,
) -> list[dict]:
    return _fetch_rows(db, start_date, end_date, project_no, changed_by, activity_type)
