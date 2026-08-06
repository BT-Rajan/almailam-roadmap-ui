from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.workflow import (
    WorkflowStageCreate,
    WorkflowStageMove,
    WorkflowStageOut,
    WorkflowStageUpdate,
    WorkflowTemplateOut,
)
from app.services import workflow_service

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Workflow templates are Administration-level configuration, same module
# the rest of the admin settings pages (users, roles) are gated behind.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/templates", response_model=list[WorkflowTemplateOut])
def list_templates(db: Session = Depends(get_db), _=Depends(can_view)):
    return [WorkflowTemplateOut.from_model(t) for t in workflow_service.list_templates(db)]


@router.post("/templates/{template_id}/stages", response_model=WorkflowStageOut, status_code=201)
def add_stage(
    template_id: str,
    payload: WorkflowStageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    stage = workflow_service.add_stage(db, template_id, payload.name, payload.description, current_user.id)
    return WorkflowStageOut.from_model(stage)


@router.patch("/stages/{stage_id}", response_model=WorkflowStageOut)
def update_stage(
    stage_id: str,
    payload: WorkflowStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    stage = workflow_service.update_stage(db, stage_id, payload.name, payload.description, current_user.id)
    return WorkflowStageOut.from_model(stage)


@router.delete("/stages/{stage_id}", status_code=204)
def remove_stage(stage_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    workflow_service.remove_stage(db, stage_id, current_user.id)


@router.post("/stages/{stage_id}/move", response_model=list[WorkflowStageOut])
def move_stage(
    stage_id: str,
    payload: WorkflowStageMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    stages = workflow_service.move_stage(db, stage_id, payload.direction, current_user.id)
    return [WorkflowStageOut.from_model(s) for s in stages]


@router.post("/templates/{template_id}/set-default", response_model=list[WorkflowTemplateOut])
def set_default_template(template_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    templates = workflow_service.set_default_template(db, template_id, current_user.id)
    return [WorkflowTemplateOut.from_model(t) for t in templates]
