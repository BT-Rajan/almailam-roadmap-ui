from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.execution_step import (
    ExecutionStepBulkUpdate,
    ExecutionStepMoveRequest,
    ExecutionStepProgressUpdate,
    ExecutionStepSetCreate,
    ExecutionStepSetOut,
    ExecutionStepSetUpdate,
    ExecutionStepTemplateCreate,
    ExecutionStepTemplateOut,
    ExecutionStepTemplateUpdate,
    ProjectCustomStepCreate,
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


# ---------------------------------------------------------------------------
# Admin: step sets
# ---------------------------------------------------------------------------


@router.get("/api/execution-step-sets", response_model=list[ExecutionStepSetOut])
def list_step_sets(db: Session = Depends(get_db), _=Depends(can_view_admin)):
    return [ExecutionStepSetOut.from_model(s) for s in execution_step_service.list_step_sets(db)]


@router.post("/api/execution-step-sets", response_model=ExecutionStepSetOut, status_code=201)
def create_step_set(
    payload: ExecutionStepSetCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit_admin)
):
    step_set = execution_step_service.create_step_set(db, payload.name, payload.description, current_user.id)
    return ExecutionStepSetOut.from_model(step_set)


@router.patch("/api/execution-step-sets/{step_set_id}", response_model=ExecutionStepSetOut)
def update_step_set(
    step_set_id: str,
    payload: ExecutionStepSetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_admin),
):
    step_set = execution_step_service.update_step_set(
        db, execution_step_service.parse_step_set_id(step_set_id), payload.name, payload.description, current_user.id
    )
    return ExecutionStepSetOut.from_model(step_set)


@router.delete("/api/execution-step-sets/{step_set_id}", status_code=204)
def delete_step_set(step_set_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit_admin)):
    execution_step_service.delete_step_set(db, execution_step_service.parse_step_set_id(step_set_id), current_user.id)


# ---------------------------------------------------------------------------
# Admin: template steps within one step set
# ---------------------------------------------------------------------------


@router.get("/api/execution-step-sets/{step_set_id}/steps", response_model=list[ExecutionStepTemplateOut])
def list_template(step_set_id: str, db: Session = Depends(get_db), _=Depends(can_view_admin)):
    steps = execution_step_service.list_template(db, execution_step_service.parse_step_set_id(step_set_id))
    return [ExecutionStepTemplateOut.from_model(s) for s in steps]


@router.post("/api/execution-step-sets/{step_set_id}/steps", response_model=ExecutionStepTemplateOut, status_code=201)
def create_template_step(
    step_set_id: str,
    payload: ExecutionStepTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_admin),
):
    step = execution_step_service.create_template_step(
        db,
        execution_step_service.parse_step_set_id(step_set_id),
        payload.name,
        payload.weightPercentage,
        payload.stageKey,
        payload.isOptional,
        payload.triggerKey,
        current_user.id,
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
        payload.triggerKey,
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


# ---------------------------------------------------------------------------
# Per-project checklist
# ---------------------------------------------------------------------------


@router.get("/api/projects/{project_no}/execution-steps", response_model=list[ProjectExecutionStepOut])
def list_project_steps(project_no: str, db: Session = Depends(get_db), _=Depends(can_view_project)):
    project = project_service.get_project(db, project_no)
    return [ProjectExecutionStepOut.from_model(s) for s in execution_step_service.list_project_steps(db, project.id)]


@router.post("/api/projects/{project_no}/execution-steps", response_model=ProjectExecutionStepOut, status_code=201)
def add_custom_project_step(
    project_no: str,
    payload: ProjectCustomStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    step = execution_step_service.add_custom_project_step(
        db, project.id, payload.name, payload.weightPercentage, payload.stageKey, current_user.id
    )
    return ProjectExecutionStepOut.from_model(step)


@router.delete("/api/projects/{project_no}/execution-steps/{step_id}", status_code=204)
def delete_custom_project_step(
    project_no: str, step_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit_project)
):
    project = project_service.get_project(db, project_no)
    execution_step_service.delete_custom_project_step(
        db, project.id, execution_step_service.parse_project_step_id(step_id), current_user.id
    )


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
