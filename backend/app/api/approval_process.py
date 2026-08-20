from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.approval_process import ProjectApprovalStepOut
from app.services import approval_process_service, project_service

router = APIRouter(tags=["approval-process"])

can_edit_project = require_permission("Projects", "edit")
can_view_project = require_permission("Projects", "view")


def _step_out(db: Session, step) -> ProjectApprovalStepOut:
    completed_by_name = None
    if step.completed_by:
        user = db.query(User).filter(User.id == step.completed_by).first()
        completed_by_name = user.full_name if user else None
    return ProjectApprovalStepOut.from_model(step, completed_by_name)


@router.get("/api/projects/{project_no}/approval-steps", response_model=list[ProjectApprovalStepOut])
def list_project_approval_steps(project_no: str, db: Session = Depends(get_db), _=Depends(can_view_project)):
    project = project_service.get_project(db, project_no)
    return [_step_out(db, s) for s in approval_process_service.list_project_steps(db, project.id)]


@router.post("/api/projects/{project_no}/approval-steps/{step_id}/complete", response_model=ProjectApprovalStepOut)
def complete_approval_step(
    project_no: str,
    step_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    step = approval_process_service.complete_step(
        db, project.id, approval_process_service.parse_project_approval_step_id(step_id), current_user.id
    )
    return _step_out(db, step)


@router.post("/api/projects/{project_no}/approval-steps/{step_id}/uncomplete", response_model=ProjectApprovalStepOut)
def uncomplete_approval_step(
    project_no: str,
    step_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    step = approval_process_service.uncomplete_step(
        db, project.id, approval_process_service.parse_project_approval_step_id(step_id), current_user.id
    )
    return _step_out(db, step)
