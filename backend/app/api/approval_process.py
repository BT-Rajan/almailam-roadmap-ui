from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
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
    uploaded_by_name = None
    if step.uploaded_by:
        user = db.query(User).filter(User.id == step.uploaded_by).first()
        uploaded_by_name = user.full_name if user else None
    return ProjectApprovalStepOut.from_model(step, uploaded_by_name)


@router.get("/api/projects/{project_no}/approval-steps", response_model=list[ProjectApprovalStepOut])
def list_project_approval_steps(project_no: str, db: Session = Depends(get_db), _=Depends(can_view_project)):
    project = project_service.get_project(db, project_no)
    return [_step_out(db, s) for s in approval_process_service.list_project_steps(db, project.id)]


@router.post("/api/projects/{project_no}/approval-steps/{stage_key}/document", response_model=ProjectApprovalStepOut)
def upload_stage_gate_document(
    project_no: str,
    stage_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    step = approval_process_service.upload_stage_gate_document(db, project.id, stage_key, file, current_user.id)
    return _step_out(db, step)


@router.get("/api/projects/{project_no}/approval-steps/{stage_key}/document")
def download_stage_gate_document(
    project_no: str, stage_key: str, db: Session = Depends(get_db), _=Depends(can_view_project)
):
    project = project_service.get_project(db, project_no)
    path, original_filename = approval_process_service.get_stage_gate_download_target(db, project.id, stage_key)
    return FileResponse(path, filename=original_filename)
