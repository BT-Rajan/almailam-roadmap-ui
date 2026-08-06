from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.task import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _project_no(db: Session, project_id: int) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.project_no if project else ""


def _to_out(db: Session, task) -> TaskOut:
    return TaskOut.from_model(task, _project_no(db, task.project_id), task_service.user_name(db, task.assigned_to))


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

    project_ids = {t.project_id for t in tasks}
    project_nos = {
        p.id: p.project_no for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
    } if project_ids else {}

    assignee_ids = {t.assigned_to for t in tasks}
    assignee_names = {
        u.id: u.full_name for u in db.query(User).filter(User.id.in_(assignee_ids)).all()
    } if assignee_ids else {}

    result["items"] = [
        TaskOut.from_model(
            t, project_nos.get(t.project_id, ""), assignee_names.get(t.assigned_to, "Unknown")
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


@router.delete("/{task_no}", status_code=204)
def delete_task(task_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    task_service.delete_task(db, task_no, current_user.id)
