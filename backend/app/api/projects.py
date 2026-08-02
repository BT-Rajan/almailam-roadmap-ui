from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectStageUpdate,
    ProjectStatusUpdate,
    ProjectUpdate,
)
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")


@router.get("", response_model=list[ProjectOut])
def list_projects(
    clientId: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    projects = project_service.list_projects(db, clientId, status, priority)
    return [ProjectOut.from_model(p, project_service.engineer_name(db, p.engineer_id)) for p in projects]


@router.get("/{project_no}", response_model=ProjectOut)
def get_project(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    return ProjectOut.from_model(project, project_service.engineer_name(db, project.engineer_id))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.create_project(db, payload, current_user.id)
    return ProjectOut.from_model(project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}", response_model=ProjectOut)
def update_project(
    project_no: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.update_project(db, project_no, payload, current_user.id)
    return ProjectOut.from_model(project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}/stage", response_model=ProjectOut)
def set_stage(
    project_no: str,
    payload: ProjectStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.set_stage(
        db, project_no, payload.currentStage, payload.reason, current_user.id
    )
    return ProjectOut.from_model(project, project_service.engineer_name(db, project.engineer_id))


@router.patch("/{project_no}/status", response_model=ProjectOut)
def set_status(
    project_no: str,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    project = project_service.set_status(
        db, project_no, payload.status, payload.reason, current_user.id
    )
    return ProjectOut.from_model(project, project_service.engineer_name(db, project.engineer_id))


@router.get("/{project_no}/audit-events")
def list_audit_events(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return project_service.get_audit_events(db, project_no)
