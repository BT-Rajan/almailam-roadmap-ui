from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.task import TaskCreate, TaskNoteCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _project_info(db: Session, project_ids: set[int]) -> dict[int, tuple[str, str, str]]:
    """project id -> (project_no, project_name, client company name), in
    one query for the whole batch."""
    if not project_ids:
        return {}
    rows = (
        db.query(Project.id, Project.project_no, Project.project_name, Client.company_name)
        .outerjoin(Client, Client.id == Project.client_id)
        .filter(Project.id.in_(project_ids))
        .all()
    )
    return {row[0]: (row[1], row[2] or "", row[3] or "") for row in rows}


def _to_out(db: Session, task) -> TaskOut:
    project_no, project_name, client_name = _project_info(db, {task.project_id}).get(task.project_id, ("", "", ""))
    return TaskOut.from_model(
        task, project_no, task_service.user_name(db, task.assigned_to), project_name, client_name,
    )


@router.get("", response_model=PagedResponse[TaskOut])
def list_tasks(
    projectId: str | None = None,
    status: str | None = None,
    assignedTo: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    result = task_service.list_tasks(db, projectId, status, assignedTo, priority, search, sort, page, pageSize)
    tasks = result["items"]

    projects = _project_info(db, {t.project_id for t in tasks})

    assignee_ids = {t.assigned_to for t in tasks}
    assignee_names = {
        u.id: u.full_name for u in db.query(User).filter(User.id.in_(assignee_ids)).all()
    } if assignee_ids else {}

    result["items"] = [
        TaskOut.from_model(
            t,
            projects.get(t.project_id, ("", "", ""))[0],
            assignee_names.get(t.assigned_to, "Unknown"),
            projects.get(t.project_id, ("", "", ""))[1],
            projects.get(t.project_id, ("", "", ""))[2],
        )
        for t in tasks
    ]
    return result


@router.get("/{task_no}", response_model=TaskOut)
def get_task(task_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, task_service.get_task(db, task_no))


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    task = task_service.create_task(db, payload, current_user.id)
    return _to_out(db, task)


@router.patch("/{task_no}", response_model=TaskOut)
def update_task(
    task_no: str, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    task = task_service.update_task(db, task_no, payload, current_user.id)
    return _to_out(db, task)


@router.patch("/{task_no}/status", response_model=TaskOut)
def set_status(
    task_no: str,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    task = task_service.set_status(db, task_no, payload.status, payload.reason, current_user.id)
    return _to_out(db, task)


@router.get("/{task_no}/audit-events")
def list_audit_events(task_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return task_service.get_audit_events(db, task_no)


@router.post("/{task_no}/notes", status_code=201)
def add_note(
    task_no: str, payload: TaskNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    return task_service.add_note(db, task_no, payload.note, current_user.id)


@router.delete("/{task_no}", status_code=204)
def delete_task(task_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    task_service.delete_task(db, task_no, current_user.id)
