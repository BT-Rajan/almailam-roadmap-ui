"""Employee Performance: how each person did against the deadlines that
fell in a chosen period.

For every task due in the period (as currently assigned), the outcome is
one of: completed on time, completed late, still open and overdue, or
not due yet (its due date is after today). Rates only count tasks that
are already due, so a period that includes the rest of this month isn't
dragged down by work that simply isn't late yet. Completion dates come
from the audit log (see report_common.completions).
"""

from sqlalchemy.orm import Session

from app.core.kuwait_time import kuwait_today
from app.models.task import Task
from app.models.user import User
from app.services.report_common import completions
from app.services.report_period import Period, kuwait_date


def employee_performance(db: Session, period: Period) -> dict:
    today = kuwait_today()
    tasks = (
        db.query(Task.id, Task.assigned_to, Task.status, Task.due_date)
        .filter(Task.deleted_at.is_(None), Task.due_date >= period.start, Task.due_date <= period.end)
        .all()
    )
    completed_ids = {task_id for task_id, _, status, _ in tasks if status == "Completed"}
    completed_at = completions(db, "TASK", None, completed_ids)
    # Completed in the period regardless of due date (throughput).
    finished_in_period = completions(db, "TASK", period)
    finished_owner = (
        dict(db.query(Task.id, Task.assigned_to).filter(Task.deleted_at.is_(None), Task.status == "Completed", Task.id.in_(finished_in_period.keys())))
        if finished_in_period
        else {}
    )

    stats: dict[int, dict] = {}

    def entry(user_id: int) -> dict:
        return stats.setdefault(user_id, {
            "due": 0, "onTime": 0, "late": 0, "overdueOpen": 0, "notYetDue": 0, "daysLate": 0, "completedInPeriod": 0,
        })

    for task_id, user_id, status, due_date in tasks:
        row = entry(user_id)
        row["due"] += 1
        if status == "Completed":
            # A task marked Completed with no recorded completion (e.g.
            # imported data) is taken as on time rather than guessed late.
            when = completed_at.get(task_id)
            late_by = (kuwait_date(when) - due_date).days if when else 0
            if late_by > 0:
                row["late"] += 1
                row["daysLate"] += late_by
            else:
                row["onTime"] += 1
        elif due_date < today:
            row["overdueOpen"] += 1
        else:
            row["notYetDue"] += 1
    for user_id in finished_owner.values():
        entry(user_id)["completedInPeriod"] += 1

    names = dict(db.query(User.id, User.full_name).filter(User.id.in_(stats.keys()))) if stats else {}
    members = []
    for user_id, row in stats.items():
        due_so_far = row["due"] - row["notYetDue"]
        members.append({
            "userId": str(user_id),
            "employeeName": names.get(user_id, "Unknown"),
            "dueInPeriod": row["due"],
            "dueSoFar": due_so_far,
            "completedOnTime": row["onTime"],
            "completedLate": row["late"],
            "overdueOpen": row["overdueOpen"],
            "notYetDue": row["notYetDue"],
            "completionRate": round((row["onTime"] + row["late"]) / due_so_far * 100, 1) if due_so_far else None,
            "onTimeRate": round(row["onTime"] / due_so_far * 100, 1) if due_so_far else None,
            "averageDaysLate": round(row["daysLate"] / row["late"], 1) if row["late"] else None,
            "completedInPeriod": row["completedInPeriod"],
        })
    members.sort(key=lambda member: (-(member["dueInPeriod"]), member["employeeName"]))

    def total(key: str) -> int:
        return sum(member[key] for member in members)

    due_so_far = total("dueSoFar")
    return {
        "period": period.as_dict(),
        "totals": {
            "dueInPeriod": total("dueInPeriod"),
            "dueSoFar": due_so_far,
            "completedOnTime": total("completedOnTime"),
            "completedLate": total("completedLate"),
            "overdueOpen": total("overdueOpen"),
            "notYetDue": total("notYetDue"),
            "completionRate": round((total("completedOnTime") + total("completedLate")) / due_so_far * 100, 1) if due_so_far else None,
            "onTimeRate": round(total("completedOnTime") / due_so_far * 100, 1) if due_so_far else None,
            "completedInPeriod": total("completedInPeriod"),
        },
        "members": members,
    }
