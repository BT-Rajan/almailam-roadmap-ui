"""Team Workload: who is carrying how much open work, who is falling
behind, who has room -- and what each person finished in a chosen period.

Open work is counted exactly as the Task Board shows it (every task not
Completed and not deleted). There is no hours/capacity field anywhere in
the data, so this reports real counts and dates only -- no invented
"utilisation" percentage.
"""

from datetime import timedelta

from sqlalchemy import case, false, func, or_
from sqlalchemy.orm import Session

from app.core.kuwait_time import kuwait_today
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services.report_common import completions
from app.services.report_period import Period, kuwait_date

DUE_SOON_DAYS = 7
NOT_STARTED_STATUSES = ("Preset", "Pending")


def team_workload(db: Session, period: Period) -> dict:
    today = kuwait_today()
    due_soon_end = today + timedelta(days=DUE_SOON_DAYS)
    open_task = (Task.deleted_at.is_(None), Task.status != "Completed")

    open_rows = (
        db.query(
            Task.assigned_to,
            func.count(Task.id),
            func.sum(case((Task.due_date < today, 1), else_=0)),
            func.sum(case(((Task.due_date >= today) & (Task.due_date < due_soon_end), 1), else_=0)),
            func.sum(case((Task.status.in_(NOT_STARTED_STATUSES), 1), else_=0)),
            func.min(case((Task.due_date < today, Task.due_date), else_=None)),
        )
        .filter(*open_task)
        .group_by(Task.assigned_to)
        .all()
    )
    open_by_user = {
        user_id: {"open": total, "overdue": int(overdue or 0), "dueSoon": int(soon or 0), "notStarted": int(not_started or 0), "oldest": oldest}
        for user_id, total, overdue, soon, not_started, oldest in open_rows
    }

    # Finished in the period: the task's latest completion, if it is still Completed.
    finished = completions(db, "TASK", period)
    done_by_user: dict[int, list[bool]] = {}
    if finished:
        for task_id, assignee, due_date in db.query(Task.id, Task.assigned_to, Task.due_date).filter(
            Task.deleted_at.is_(None), Task.status == "Completed", Task.id.in_(finished.keys())
        ):
            done_by_user.setdefault(assignee, []).append(kuwait_date(finished[task_id]) <= due_date)

    projects_by_user = dict(
        db.query(Project.engineer_id, func.count(Project.id))
        .filter(Project.deleted_at.is_(None), Project.status == "Active")
        .group_by(Project.engineer_id)
        .all()
    )

    # Everyone who has work to show, plus every active engineer (an idle
    # engineer is exactly the "who has room" answer). A deactivated or
    # deleted user still holding open tasks is included and flagged: that
    # work is stranded until someone reassigns it.
    involved = set(open_by_user) | set(done_by_user)
    users = (
        db.query(User)
        .filter(
            or_(
                User.id.in_(involved) if involved else false(),
                (User.role == "Engineer") & User.is_active.is_(True) & User.deleted_at.is_(None),
            )
        )
        .all()
    )

    members = []
    for user in users:
        open_work = open_by_user.get(user.id, {"open": 0, "overdue": 0, "dueSoon": 0, "notStarted": 0, "oldest": None})
        done = done_by_user.get(user.id, [])
        members.append({
            "userId": str(user.id),
            "name": user.full_name,
            "role": user.role,
            "inactive": (not user.is_active) or user.deleted_at is not None,
            "activeProjects": projects_by_user.get(user.id, 0),
            "openTasks": open_work["open"],
            "overdueTasks": open_work["overdue"],
            "dueSoonTasks": open_work["dueSoon"],
            "laterTasks": open_work["open"] - open_work["overdue"] - open_work["dueSoon"],
            "notStartedTasks": open_work["notStarted"],
            "oldestOverdueDays": (today - open_work["oldest"]).days if open_work["oldest"] else None,
            "completedInPeriod": len(done),
            "onTimeRate": round(sum(done) / len(done) * 100, 1) if done else None,
        })
    # Heaviest load first; ties by name for a stable order.
    members.sort(key=lambda member: (-member["openTasks"], -member["overdueTasks"], member["name"]))

    completed = sum(member["completedInPeriod"] for member in members)
    on_time = sum(sum(done_by_user.get(int(member["userId"]), [])) for member in members)
    open_total = sum(member["openTasks"] for member in members)
    overdue_total = sum(member["overdueTasks"] for member in members)
    return {
        "period": period.as_dict(),
        "dueSoonDays": DUE_SOON_DAYS,
        "totals": {
            "people": len(members),
            "peopleWithOpenWork": sum(1 for member in members if member["openTasks"] > 0),
            "peopleWithOverdue": sum(1 for member in members if member["overdueTasks"] > 0),
            "openTasks": open_total,
            "overdueTasks": overdue_total,
            "overdueShare": round(overdue_total / open_total * 100, 1) if open_total else None,
            "dueSoonTasks": sum(member["dueSoonTasks"] for member in members),
            "completedInPeriod": completed,
            "onTimeRate": round(on_time / completed * 100, 1) if completed else None,
            "strandedTasks": sum(member["openTasks"] for member in members if member["inactive"]),
        },
        "members": members,
    }
