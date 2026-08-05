from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.status_transitions import TASK_ALLOWED_TRANSITIONS, TASK_STATUSES_REQUIRING_REASON
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import audit_service, notification_service, user_service
from app.services.number_series_service import next_number

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


def list_tasks(
    db: Session,
    project_no: str | None = None,
    status: str | None = None,
    assigned_to: str | None = None,
    priority: str | None = None,
) -> list[Task]:
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
    return query.order_by(Task.due_date.asc(), Task.due_time.asc()).all()


def get_task(db: Session, task_no: str) -> Task:
    task = db.query(Task).filter(Task.task_no == task_no, Task.deleted_at.is_(None)).first()
    if task is None:
        raise NotFoundError("Task")
    return task


def create_task(db: Session, payload, user_id: int) -> Task:
    project = _project_by_no(db, payload.projectId)
    assignee_id = _resolve_assignee(db, payload.assignedTo)

    task = Task(
        task_no=next_number(db, "TASK"),
        project_id=project.id,
        title=payload.title,
        assigned_to=assignee_id,
        priority=payload.priority,
        severity=payload.severity,
        due_date=payload.dueDate,
        due_time=payload.dueTime,
    )
    db.add(task)
    db.flush()

    audit_service.log_event(db, ENTITY_TYPE, task.id, "Task created", user_id)
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

    audit_service.log_field_changes(db, ENTITY_TYPE, task.id, changes, user_id)
    db.commit()
    db.refresh(task)
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
    db.commit()
    db.refresh(task)
    return task


def get_audit_events(db: Session, task_no: str) -> list[dict]:
    task = get_task(db, task_no)
    return audit_service.get_history(db, ENTITY_TYPE, task.id)
