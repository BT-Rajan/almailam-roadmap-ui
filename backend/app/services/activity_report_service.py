"""Employee Activity: what each person actually did in a chosen period,
and in which parts of the system -- summarised from the audit log (the
same rows the Activity Calendar and Audit Log show), so only per-person
and per-period counts travel to the browser, not every row.
"""

from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.services import activity_service
from app.services.report_period import Period, bucketer, buckets, granularity

AREAS = ("task", "project", "document", "payment", "client", "quotation", "contract", "workflow")
SYSTEM_USER = ""


def employee_activity(db: Session, period: Period, user_id: int | None = None) -> dict:
    rows = activity_service.get_filtered_activities(db, period.start, period.end + timedelta(days=1), changed_by=user_id)

    bucket_list = buckets(period)
    index_of = bucketer(bucket_list)

    per_person: dict[str, dict] = {}
    series = [0] * len(bucket_list)
    by_area: Counter = Counter()
    days_by_person: dict[str, set] = defaultdict(set)
    projects_by_person: dict[str, set] = defaultdict(set)
    for row in rows:
        key = row["userId"] or SYSTEM_USER
        person = per_person.get(key)
        if person is None:
            person = per_person[key] = {
                "userId": key,
                "name": row["userName"],
                "system": key == SYSTEM_USER,
                "actions": 0,
                "byType": Counter(),
                "byArea": Counter(),
                "lastActivity": row["timestamp"],  # rows arrive newest first
            }
        person["actions"] += 1
        person["byType"][row["type"]] += 1
        person["byArea"][row["entityType"]] += 1
        days_by_person[key].add(row["kuwaitDate"])
        if row["projectId"]:
            projects_by_person[key].add(row["projectId"])
        by_area[row["entityType"]] += 1
        index = index_of(date.fromisoformat(row["kuwaitDate"]))
        if index is not None:
            series[index] += 1

    members = []
    for key, person in per_person.items():
        members.append({
            "userId": person["userId"],
            "name": person["name"],
            "system": person["system"],
            "actions": person["actions"],
            "activeDays": len(days_by_person[key]),
            "projectsTouched": len(projects_by_person[key]),
            "created": person["byType"]["new"],
            "updated": person["byType"]["updated"] + person["byType"]["assigned"] + person["byType"]["commented"],
            "completed": person["byType"]["completed"] + person["byType"]["approved"],
            "rejected": person["byType"]["rejected"],
            "deleted": person["byType"]["deleted"],
            "byArea": {area: person["byArea"][area] for area in AREAS},
            "lastActivity": person["lastActivity"],
        })
    members.sort(key=lambda member: (member["system"], -member["actions"], member["name"]))

    people = [member for member in members if not member["system"]]
    total_actions = sum(member["actions"] for member in people)
    return {
        "period": period.as_dict(),
        "bucket": granularity(period),
        "totals": {
            "actions": total_actions,
            "systemActions": sum(member["actions"] for member in members if member["system"]),
            "peopleActive": len(people),
            "created": sum(member["created"] for member in people),
            "completed": sum(member["completed"] for member in people),
            "deleted": sum(member["deleted"] for member in people),
        },
        "series": {"categories": [bucket.label for bucket in bucket_list], "actions": series},
        "areas": [{"label": area, "value": by_area[area]} for area in AREAS if by_area[area]],
        "members": members,
    }
