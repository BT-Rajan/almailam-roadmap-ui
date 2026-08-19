from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.project_link_document import ProjectLinkDocumentCreate, ProjectLinkDocumentOut
from app.services import project_link_document_service as link_service

router = APIRouter(prefix="/api/projects", tags=["project-link-documents"])

can_view = require_permission("Documents", "view")
can_edit = require_permission("Documents", "edit")
can_delete = require_permission("Documents", "delete")


def _out(db: Session, document, project_no: str) -> ProjectLinkDocumentOut:
    return ProjectLinkDocumentOut.from_model(document, project_no, link_service.user_name(db, document.added_by))


@router.get("/{project_no}/link-documents", response_model=list[ProjectLinkDocumentOut])
def list_link_documents(
    project_no: str,
    category: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    return [_out(db, document, project_no) for document in link_service.list_for_project(db, project_no, category)]


@router.post("/{project_no}/link-documents", response_model=ProjectLinkDocumentOut, status_code=201)
def create_link_document(
    project_no: str,
    payload: ProjectLinkDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = link_service.add_link_document(db, project_no, payload, current_user.id)
    return _out(db, document, project_no)


@router.delete("/{project_no}/link-documents/{link_document_no}", status_code=204)
def delete_link_document(
    project_no: str,
    link_document_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_delete),
):
    link_service.delete_link_document(db, link_document_no, current_user.id)
