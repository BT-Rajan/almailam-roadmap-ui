from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.file_storage import format_file_size
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.document import (
    DocumentAIReviewCreate,
    DocumentAIReviewOut,
    DocumentOut,
    DocumentStatusUpdate,
    DocumentUpdate,
    DocumentVersionOut,
)
from app.services import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])

can_view = require_permission("Documents", "view")
can_edit = require_permission("Documents", "edit")
can_delete = require_permission("Documents", "delete")


def _project_no(db: Session, project_id: int) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.project_no if project else ""


def _document_out(db: Session, document) -> DocumentOut:
    return DocumentOut.from_model(
        document,
        _project_no(db, document.project_id),
        document_service.user_name(db, document.uploaded_by),
        format_file_size(document.file_size_bytes),
    )


@router.get("", response_model=PagedResponse[DocumentOut])
def list_documents(
    projectId: str | None = None,
    status: str | None = None,
    type: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    result = document_service.list_documents(db, projectId, status, type, search, sort, page, pageSize)
    documents = result["items"]

    project_ids = {d.project_id for d in documents}
    project_nos = {
        p.id: p.project_no for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
    } if project_ids else {}

    uploader_ids = {d.uploaded_by for d in documents}
    uploader_names = {
        u.id: u.full_name for u in db.query(User).filter(User.id.in_(uploader_ids)).all()
    } if uploader_ids else {}

    result["items"] = [
        DocumentOut.from_model(
            d,
            project_nos.get(d.project_id, ""),
            uploader_names.get(d.uploaded_by, "Unknown"),
            format_file_size(d.file_size_bytes),
        )
        for d in documents
    ]
    return result


@router.get("/{document_no}", response_model=DocumentOut)
def get_document(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _document_out(db, document_service.get_document(db, document_no))


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(
    projectId: str = Form(...),
    title: str = Form(...),
    type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = document_service.create_document(db, projectId, title, type, file, current_user.id)
    return _document_out(db, document)


@router.patch("/{document_no}", response_model=DocumentOut)
def update_document(
    document_no: str,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = document_service.update_document(db, document_no, payload, current_user.id)
    return _document_out(db, document)


@router.patch("/{document_no}/status", response_model=DocumentOut)
def set_status(
    document_no: str,
    payload: DocumentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = document_service.set_status(db, document_no, payload.status, payload.reason, current_user.id)
    return _document_out(db, document)


@router.get("/{document_no}/download")
def download_document(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = document_service.get_download_target(db, document_no)
    return FileResponse(path, filename=original_filename)


@router.get("/{document_no}/versions", response_model=list[DocumentVersionOut])
def list_versions(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    document = document_service.get_document(db, document_no)
    versions = document_service.get_versions(db, document.id)
    return [
        DocumentVersionOut.from_model(v, document.id, document.document_no, document_service.user_name(db, v.uploaded_by))
        for v in versions
    ]


@router.get("/{document_no}/versions/{version_id}/download")
def download_version(document_no: str, version_id: int, db: Session = Depends(get_db), _=Depends(can_view)):
    path, original_filename = document_service.get_version_download_target(db, document_no, version_id)
    return FileResponse(path, filename=original_filename)


@router.post("/{document_no}/versions", response_model=DocumentVersionOut, status_code=201)
def add_version(
    document_no: str,
    file: UploadFile = File(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = document_service.get_document(db, document_no)
    version = document_service.add_version(db, document_no, file, notes, current_user.id)
    return DocumentVersionOut.from_model(version, document.id, document.document_no, current_user.full_name)


@router.get("/{document_no}/ai-review", response_model=DocumentAIReviewOut | None)
def get_ai_review(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    document = document_service.get_document(db, document_no)
    review = document_service.get_ai_review(db, document.id)
    return DocumentAIReviewOut.from_model(review, document_no) if review else None


@router.post("/{document_no}/ai-review", response_model=DocumentAIReviewOut, status_code=201)
def create_ai_review(
    document_no: str,
    payload: DocumentAIReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    review = document_service.create_ai_review(db, document_no, payload, current_user.id)
    return DocumentAIReviewOut.from_model(review, document_no)


@router.get("/{document_no}/audit-events")
def list_audit_events(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return document_service.get_audit_events(db, document_no)


@router.delete("/{document_no}", status_code=204)
def delete_document(document_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    document_service.delete_document(db, document_no, current_user.id)
