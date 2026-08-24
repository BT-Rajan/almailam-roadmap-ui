from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.execution_step import (
    ExecutionStepBulkUpdate,
    ExecutionStepMoveRequest,
    ExecutionStepProgressUpdate,
    ExecutionStepTemplateCreate,
    ExecutionStepTemplateOut,
    ExecutionStepTemplateUpdate,
    ProjectExecutionStepOut,
)
from app.services import execution_step_service, project_service

router = APIRouter(tags=["execution-steps"])

# Admin template management -- same module the workflow templates and
# service catalog are gated behind.
can_view_admin = require_permission("Administration", "view")
can_edit_admin = require_permission("Administration", "edit")

# Marking a project's own checklist steps complete is ordinary project
# work, not an admin action -- same permission as any other project
# mutation.
can_edit_project = require_permission("Projects", "edit")
can_view_project = require_permission("Projects", "view")


@router.get("/api/execution-step-template", response_model=list[ExecutionStepTemplateOut])
def list_template(db: Session = Depends(get_db), _=Depends(can_view_admin)):
    return [ExecutionStepTemplateOut.from_model(s) for s in execution_step_service.list_template(db)]


@router.post("/api/execution-step-template", response_model=ExecutionStepTemplateOut, status_code=201)
def create_template_step(
    payload: ExecutionStepTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_admin),
):
    step = execution_step_service.create_template_step(
        db, payload.name, payload.weightPercentage, payload.stageKey, payload.isOptional, current_user.id
    )
    return ExecutionStepTemplateOut.from_model(step)


@router.patch("/api/execution-step-template/{step_id}", response_model=ExecutionStepTemplateOut)
def update_template_step(
    step_id: str,
    payload: ExecutionStepTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_admin),
):
    step = execution_step_service.update_template_step(
        db,
        execution_step_service.parse_template_step_id(step_id),
        payload.name,
        payload.weightPercentage,
        payload.stageKey,
        payload.isOptional,
        current_user.id,
    )
    return ExecutionStepTemplateOut.from_model(step)


@router.delete("/api/execution-step-template/{step_id}", status_code=204)
def delete_template_step(step_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit_admin)):
    execution_step_service.delete_template_step(db, execution_step_service.parse_template_step_id(step_id), current_user.id)


@router.post("/api/execution-step-template/{step_id}/move", response_model=list[ExecutionStepTemplateOut])
def move_template_step(
    step_id: str,
    payload: ExecutionStepMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_admin),
):
    steps = execution_step_service.move_template_step(
        db, execution_step_service.parse_template_step_id(step_id), payload.direction, current_user.id
    )
    return [ExecutionStepTemplateOut.from_model(s) for s in steps]


@router.get("/api/projects/{project_no}/execution-steps", response_model=list[ProjectExecutionStepOut])
def list_project_steps(project_no: str, db: Session = Depends(get_db), _=Depends(can_view_project)):
    project = project_service.get_project(db, project_no)
    return [ProjectExecutionStepOut.from_model(s) for s in execution_step_service.list_project_steps(db, project.id)]


@router.patch("/api/projects/{project_no}/execution-steps/{step_id}/progress", response_model=ProjectExecutionStepOut)
def set_step_progress(
    project_no: str,
    step_id: str,
    payload: ExecutionStepProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    step = execution_step_service.set_step_progress(
        db, project.id, execution_step_service.parse_project_step_id(step_id),
        payload.completionPercentage, payload.remarks, current_user.id,
    )
    return ProjectExecutionStepOut.from_model(step)


@router.patch("/api/projects/{project_no}/execution-steps", response_model=list[ProjectExecutionStepOut])
def bulk_update_project_steps(
    project_no: str,
    payload: ExecutionStepBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    """The checklist's single Save button -- saves every changed
    activity (progress, remarks, excluded/reason) in one call."""
    project = project_service.get_project(db, project_no)
    parsed_items = [
        (execution_step_service.parse_project_step_id(item.id), item) for item in payload.steps
    ]
    steps = execution_step_service.bulk_set_steps(db, project.id, parsed_items, current_user.id)
    return [ProjectExecutionStepOut.from_model(s) for s in steps]
