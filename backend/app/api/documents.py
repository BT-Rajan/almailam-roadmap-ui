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


def _projects(db: Session, project_ids: set[int]) -> dict[int, tuple[str, str]]:
    """project id -> (project_no, project_name), one query for the batch."""
    if not project_ids:
        return {}
    rows = db.query(Project.id, Project.project_no, Project.project_name).filter(Project.id.in_(project_ids)).all()
    return {row[0]: (row[1], row[2]) for row in rows}


def _document_out(db: Session, document) -> DocumentOut:
    project_no, project_name = _projects(db, {document.project_id}).get(document.project_id, ("", ""))
    return DocumentOut.from_model(
        document,
        project_no,
        document_service.user_name(db, document.uploaded_by),
        format_file_size(document.file_size_bytes) if document.file_size_bytes is not None else None,
        project_name,
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

    projects = _projects(db, {d.project_id for d in documents})

    uploader_ids = {d.uploaded_by for d in documents}
    uploader_names = {
        u.id: u.full_name for u in db.query(User).filter(User.id.in_(uploader_ids)).all()
    } if uploader_ids else {}

    result["items"] = [
        DocumentOut.from_model(
            d,
            projects.get(d.project_id, ("", ""))[0],
            uploader_names.get(d.uploaded_by, "Unknown"),
            format_file_size(d.file_size_bytes) if d.file_size_bytes is not None else None,
            projects.get(d.project_id, ("", ""))[1],
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
    externalLink: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = document_service.create_document(
        db, projectId, title, type, file, current_user.id, externalLink
    )
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
        DocumentVersionOut.from_model(v, document.document_no, document_service.user_name(db, v.uploaded_by))
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
    return DocumentVersionOut.from_model(version, document.document_no, current_user.full_name)


@router.get("/{document_no}/audit-events")
def list_audit_events(document_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return document_service.get_audit_events(db, document_no)


@router.delete("/{document_no}", status_code=204)
def delete_document(document_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    document_service.delete_document(db, document_no, current_user.id)
