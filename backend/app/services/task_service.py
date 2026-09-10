from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import TASK_ALLOWED_TRANSITIONS, TASK_STATUSES_REQUIRING_REASON
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import audit_service, notification_service, project_service, timeline_service, user_service
from app.services.number_series_service import next_task_number

ENTITY_TYPE = "TASK"


def user_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "Unassigned"
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def _resolve_assignee(db: Session, raw_user_id: str) -> int:
    user_id = user_service.parse_user_id(raw_user_id)
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise ValidationAppError("assignedTo does not refer to a known user.")
    return user_id


def _resolve_selected_activity(db: Session, project_id: int, raw_activity_id: str) -> int:
    """Resolves and validates selectedActivityId against the task's own
    project -- reuses project_service.get_selected_activity, which
    already scopes the lookup to project_id, so a task can't be linked
    to another project's activity by guessing its raw id."""
    if not raw_activity_id.isdigit():
        raise ValidationAppError("selectedActivityId must be a valid id.")
    activity = project_service.get_selected_activity(db, project_id, int(raw_activity_id))
    return activity.id


TASK_SORTABLE_FIELDS = {
    "title": Task.title,
    "status": Task.status,
    "priority": Task.priority,
    "severity": Task.severity,
    "dueDate": Task.due_date,
}


def list_tasks(
    db: Session,
    project_no: str | None = None,
    status: str | None = None,
    assigned_to: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    query = db.query(Task).filter(Task.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(Task.project_id == (project.id if project else -1))
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        query = query.filter(Task.assigned_to == user_service.parse_user_id(assigned_to))
    if priority:
        query = query.filter(Task.priority == priority)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Task.task_no.ilike(term), Task.title.ilike(term)))
    # Tasks default to soonest-due-first, unlike the id-desc default most
    # other lists use, so pass an explicit ascending sort when the caller
    # didn't request one, rather than relying on sort_and_paginate's
    # (descending) fallback.
    return sort_and_paginate(query, Task, TASK_SORTABLE_FIELDS, sort or "dueDate", page, page_size)


def get_task(db: Session, task_no: str) -> Task:
    task = db.query(Task).filter(Task.task_no == task_no, Task.deleted_at.is_(None)).first()
    if task is None:
        raise NotFoundError("Task")
    return task


def create_task(db: Session, payload, user_id: int) -> Task:
    project = _project_by_no(db, payload.projectId)
    project_service.assert_project_open_for_new_work(project)
    assignee_id = _resolve_assignee(db, payload.assignedTo)
    selected_activity_id = (
        _resolve_selected_activity(db, project.id, payload.selectedActivityId)
        if payload.selectedActivityId is not None
        else None
    )

    task = Task(
        task_no=next_task_number(db, project.id, project.project_no),
        project_id=project.id,
        selected_activity_id=selected_activity_id,
        title=payload.title,
        assigned_to=assignee_id,
        priority=payload.priority,
        severity=payload.severity,
        start_date=payload.startDate,
        due_date=payload.dueDate,
        due_time=payload.dueTime,
    )
    db.add(task)
    db.flush()

    audit_service.log_event(db, ENTITY_TYPE, task.id, "Task created", user_id, new_value=task.title)
    timeline_service.create_system_event(
        db, project.id, "task",
        title=f"Task created: {task.title}",
        actor_id=user_id,
    )
    notification_service.create_notification(
        db, assignee_id, "New task assigned", f"You've been assigned: {payload.title}", "Task",
        link_route_name="tasks",
    )
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_no: str, payload, user_id: int) -> Task:
    task = get_task(db, task_no)
    changes: dict[str, tuple] = {}

    for api_field, attr in (
        ("title", "title"),
        ("priority", "priority"),
        ("severity", "severity"),
        ("startDate", "start_date"),
        ("dueDate", "due_date"),
        ("dueTime", "due_time"),
    ):
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(task, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(task, attr, value)

    if payload.assignedTo is not None:
        new_assignee_id = _resolve_assignee(db, payload.assignedTo)
        if new_assignee_id != task.assigned_to:
            changes["assigned_to"] = (task.assigned_to, new_assignee_id)
            task.assigned_to = new_assignee_id
            notification_service.create_notification(
                db, new_assignee_id, "Task reassigned to you", f"You've been assigned: {task.title}", "Task",
                link_route_name="tasks",
            )

    if payload.selectedActivityId is not None:
        new_activity_id = _resolve_selected_activity(db, task.project_id, payload.selectedActivityId)
        if new_activity_id != task.selected_activity_id:
            changes["selected_activity_id"] = (task.selected_activity_id, new_activity_id)
            task.selected_activity_id = new_activity_id

    # A 'Preset' service task (see project_service._create_service_tasks)
    # graduates to 'Pending' the moment anything about it actually
    # changes here -- the normal, expected way out of Preset (being
    # reviewed and given a real owner/date), distinct from an explicit
    # status change via set_status below.
    if task.status == "Preset" and changes:
        changes["status"] = (task.status, "Pending")
        task.status = "Pending"

    audit_service.log_field_changes(db, ENTITY_TYPE, task.id, changes, user_id)
    db.commit()
    db.refresh(task)

    if payload.status is not None and payload.status != task.status:
        task = set_status(db, task_no, payload.status, payload.reason, user_id)

    return task


def set_status(db: Session, task_no: str, new_status: str, reason: str | None, user_id: int) -> Task:
    task = get_task(db, task_no)
    assert_transition_allowed(TASK_ALLOWED_TRANSITIONS, task.status, new_status, "task")
    if new_status in TASK_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the task to '{new_status}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, task.id, "Status changed", user_id,
        previous_value=task.status, new_value=new_status, reason=reason,
    )
    task.status = new_status
    if new_status == "Completed":
        # Closing the last task linked to a Design activity/Permit/
        # Supervision activity auto-closes it -- see project_service.
        # maybe_auto_close_design_activity/maybe_auto_close_permit/
        # maybe_auto_close_supervision_activity, each of which no-ops if
        # other linked tasks are still open or it was already closed by
        # hand. A task is linked to at most one of the three.
        if task.selected_activity_id is not None:
            project_service.maybe_auto_close_design_activity(db, task.selected_activity_id, user_id)
        if task.selected_permit_id is not None:
            project_service.maybe_auto_close_permit(db, task.selected_permit_id, user_id)
        if task.selected_supervision_activity_id is not None:
            project_service.maybe_auto_close_supervision_activity(db, task.selected_supervision_activity_id, user_id)
        # "Every task closed" is itself one of Handover's own exit
        # criteria (see project_service._assert_stage_exit_criteria),
        # independent of whichever activity/permit/supervision item the
        # task happens to be linked to (or not linked to at all -- a
        # generic task counts too). The three calls above only ever
        # re-check the stage when they actually close a linked item, so
        # completing the *last* open task -- generic, or one whose
        # activity/permit/supervision was already closed earlier by
        # hand -- was never re-triggering this check on its own,
        # leaving a project stuck just short of Handover even once
        # every real condition was already satisfied. try_auto_advance_
        # stage is a safe, idempotent no-op when the exit criteria
        # aren't met yet, so calling it unconditionally here as well
        # costs nothing on every other task completion.
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if project is not None:
            db.flush()
            project_service.try_auto_advance_stage(db, project, user_id)
    db.commit()
    db.refresh(task)
    return task


def _task_exists(db: Session, task_no: str) -> Task:
    """Like get_task() but doesn't exclude soft-deleted tasks -- used
    only for the read-only audit-trail view."""
    task = db.query(Task).filter(Task.task_no == task_no).first()
    if task is None:
        raise NotFoundError("Task")
    return task


def get_audit_events(db: Session, task_no: str) -> list[dict]:
    task = _task_exists(db, task_no)
    return audit_service.get_history(db, ENTITY_TYPE, task.id)


def delete_task(db: Session, task_no: str, actor_id: int) -> None:
    task = get_task(db, task_no)
    audit_service.log_event(db, ENTITY_TYPE, task.id, "Task deleted", actor_id, previous_value=task.title)
    task.deleted_at = datetime.now(timezone.utc)
    db.commit()
