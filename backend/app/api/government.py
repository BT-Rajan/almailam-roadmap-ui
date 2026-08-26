from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.file_storage import format_file_size
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentOut
from app.schemas.government import (
    AuthorityIn,
    AuthorityOut,
    FormFillRequest,
    FormIn,
    FormOut,
    FormStatusUpdate,
)
from app.services import document_service, government_service

router = APIRouter(prefix="/api/government", tags=["government"])

can_view = require_permission("Government", "view")
can_edit = require_permission("Government", "edit")


def _project_no(db: Session, project_id: int) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.project_no if project else ""


@router.get("/authorities", response_model=list[AuthorityOut])
def list_authorities(db: Session = Depends(get_db), _=Depends(can_view)):
    return [AuthorityOut.from_model(a) for a in government_service.list_authorities(db)]


@router.post("/authorities", response_model=AuthorityOut, status_code=201)
def create_authority(
    payload: AuthorityIn, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    return AuthorityOut.from_model(
        government_service.create_authority(db, payload, current_user.id)
    )


@router.patch("/authorities/{authority_id}", response_model=AuthorityOut)
def update_authority(
    authority_id: str,
    payload: AuthorityIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    authority = government_service.update_authority(
        db, government_service.parse_authority_id(authority_id), payload, current_user.id
    )
    return AuthorityOut.from_model(authority)


@router.delete("/authorities/{authority_id}", status_code=204)
def delete_authority(
    authority_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    government_service.delete_authority(
        db, government_service.parse_authority_id(authority_id), current_user.id
    )


@router.get("/forms", response_model=list[FormOut])
def list_forms(
    authorityId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    authority_id = government_service.parse_authority_id(authorityId) if authorityId else None
    return [
        FormOut.from_model(f) for f in government_service.list_forms(db, authority_id, status)
    ]


@router.post("/forms", response_model=FormOut, status_code=201)
def create_form(
    payload: FormIn, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    return FormOut.from_model(government_service.create_form(db, payload, current_user.id))


@router.patch("/forms/{form_id}", response_model=FormOut)
def update_form(
    form_id: str,
    payload: FormIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    form = government_service.update_form(
        db, government_service.parse_form_id(form_id), payload, current_user.id
    )
    return FormOut.from_model(form)


@router.delete("/forms/{form_id}", status_code=204)
def delete_form(
    form_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    government_service.delete_form(db, government_service.parse_form_id(form_id), current_user.id)


@router.post("/forms/{form_id}/fill", response_model=DocumentOut, status_code=201)
def fill_form(
    form_id: str,
    payload: FormFillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = government_service.fill_form(
        db, government_service.parse_form_id(form_id), payload, current_user.id
    )
    return DocumentOut.from_model(
        document,
        _project_no(db, document.project_id),
        document_service.user_name(db, document.uploaded_by),
        format_file_size(document.file_size_bytes) if document.file_size_bytes is not None else None,
    )


@router.patch("/forms/{form_id}/status", response_model=FormOut)
def set_form_status(
    form_id: str,
    payload: FormStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    form = government_service.set_form_status(
        db, government_service.parse_form_id(form_id), payload.status, current_user.id
    )
    return FormOut.from_model(form)
