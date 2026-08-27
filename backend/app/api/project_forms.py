from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.document import ProjectDocument
from app.models.user import User
from app.schemas.government import (
    ProjectFormEntryCreate,
    ProjectFormEntryOut,
    ProjectFormEntryStatusUpdate,
    ProjectFormEntryUpdate,
)
from app.services import document_service, government_service, project_form_service, project_service

router = APIRouter(tags=["project-form-entries"])

can_edit_project = require_permission("Projects", "edit")
can_view_project = require_permission("Projects", "view")


def _entry_out(db: Session, entry) -> ProjectFormEntryOut:
    form = government_service.get_form(db, entry.form_id)
    authority = government_service.get_authority(db, form.authority_id)
    document_no = None
    if entry.document_id:
        document = db.query(ProjectDocument).filter(ProjectDocument.id == entry.document_id).first()
        document_no = document.document_no if document else None
    created_by_name = document_service.user_name(db, entry.created_by) if entry.created_by else None
    return ProjectFormEntryOut.from_model(entry, form, authority, document_no, created_by_name)


@router.get("/api/projects/{project_no}/form-entries", response_model=list[ProjectFormEntryOut])
def list_form_entries(project_no: str, db: Session = Depends(get_db), _=Depends(can_view_project)):
    project = project_service.get_project(db, project_no)
    return [_entry_out(db, e) for e in project_form_service.list_project_form_entries(db, project.id)]


@router.post("/api/projects/{project_no}/form-entries", response_model=ProjectFormEntryOut, status_code=201)
def create_form_entry(
    project_no: str,
    payload: ProjectFormEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    entry = project_form_service.create_project_form_entry(
        db, project, government_service.parse_form_id(payload.formId), payload.fieldValues, current_user.id
    )
    return _entry_out(db, entry)


@router.patch("/api/projects/{project_no}/form-entries/{entry_id}", response_model=ProjectFormEntryOut)
def update_form_entry(
    project_no: str,
    entry_id: str,
    payload: ProjectFormEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    entry = project_form_service.update_project_form_entry(
        db, project, project_form_service.parse_entry_id(entry_id), payload.fieldValues, current_user.id
    )
    return _entry_out(db, entry)


@router.patch("/api/projects/{project_no}/form-entries/{entry_id}/status", response_model=ProjectFormEntryOut)
def update_form_entry_status(
    project_no: str,
    entry_id: str,
    payload: ProjectFormEntryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit_project),
):
    project = project_service.get_project(db, project_no)
    entry = project_form_service.set_project_form_entry_status(
        db, project.id, project_form_service.parse_entry_id(entry_id), payload.status, current_user.id
    )
    return _entry_out(db, entry)


@router.delete("/api/projects/{project_no}/form-entries/{entry_id}", status_code=204)
def delete_form_entry(
    project_no: str, entry_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit_project)
):
    project = project_service.get_project(db, project_no)
    project_form_service.delete_project_form_entry(
        db, project.id, project_form_service.parse_entry_id(entry_id), current_user.id
    )
