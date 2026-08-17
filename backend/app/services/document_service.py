from datetime import date, datetime, timezone

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    DOCUMENT_ALLOWED_TRANSITIONS,
    DOCUMENT_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.document import DocumentAIReview, DocumentVersion, ProjectDocument
from app.models.project import Project
from app.models.user import User
from app.services import audit_service, notification_service, project_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "DOCUMENT"


def user_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "System"
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def _next_revision_label(current: str) -> str:
    letter = current.replace("Rev ", "").strip().upper()
    if len(letter) == 1 and letter.isalpha() and letter != "Z":
        return f"Rev {chr(ord(letter) + 1)}"
    return "Rev B"


DOCUMENT_SORTABLE_FIELDS = {
    "title": ProjectDocument.title,
    "type": ProjectDocument.type,
    "status": ProjectDocument.status,
    "uploadDate": ProjectDocument.upload_date,
    "revision": ProjectDocument.revision,
}


def list_documents(
    db: Session,
    project_no: str | None = None,
    status: str | None = None,
    doc_type: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    query = db.query(ProjectDocument).filter(ProjectDocument.deleted_at.is_(None))
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(ProjectDocument.project_id == (project.id if project else -1))
    if status:
        query = query.filter(ProjectDocument.status == status)
    if doc_type:
        query = query.filter(ProjectDocument.type == doc_type)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(ProjectDocument.document_no.ilike(term), ProjectDocument.title.ilike(term))
        )
    return sort_and_paginate(query, ProjectDocument, DOCUMENT_SORTABLE_FIELDS, sort, page, page_size)


def get_document(db: Session, document_no: str) -> ProjectDocument:
    document = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.document_no == document_no, ProjectDocument.deleted_at.is_(None))
        .first()
    )
    if document is None:
        raise NotFoundError("Document")
    return document


def create_document(
    db: Session, project_no: str, title: str, doc_type: str, file: UploadFile, user_id: int
) -> ProjectDocument:
    project = _project_by_no(db, project_no)
    project_service.assert_project_open_for_new_work(project)
    storage_key, original_filename, size_bytes = save_upload(file, "documents")

    document = ProjectDocument(
        document_no=next_number(db, "DOCUMENT"),
        project_id=project.id,
        title=title,
        type=doc_type,
        uploaded_by=user_id,
        upload_date=date.today(),
        storage_key=storage_key,
        original_filename=original_filename,
        file_size_bytes=size_bytes,
    )
    db.add(document)
    db.flush()

    audit_service.log_event(db, ENTITY_TYPE, document.id, "Document uploaded", user_id)
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, document_no: str, payload, user_id: int) -> ProjectDocument:
    document = get_document(db, document_no)
    changes: dict[str, tuple] = {}
    if payload.title is not None and payload.title != document.title:
        changes["title"] = (document.title, payload.title)
        document.title = payload.title

    audit_service.log_field_changes(db, ENTITY_TYPE, document.id, changes, user_id)
    db.commit()
    db.refresh(document)
    return document


def set_status(db: Session, document_no: str, new_status: str, reason: str | None, user_id: int) -> ProjectDocument:
    document = get_document(db, document_no)
    assert_transition_allowed(DOCUMENT_ALLOWED_TRANSITIONS, document.status, new_status, "document")
    if new_status in DOCUMENT_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the document to '{new_status}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, document.id, "Status changed", user_id,
        previous_value=document.status, new_value=new_status, reason=reason,
    )
    document.status = new_status
    db.commit()
    db.refresh(document)
    return document


def get_versions(db: Session, document_id: int) -> list[DocumentVersion]:
    return (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.id.asc())
        .all()
    )


def add_version(db: Session, document_no: str, file: UploadFile, notes: str, user_id: int) -> DocumentVersion:
    document = get_document(db, document_no)

    db.add(
        DocumentVersion(
            document_id=document.id,
            revision=document.revision,
            uploaded_by=document.uploaded_by,
            upload_date=document.upload_date,
            notes="Initial upload." if document.revision == "Rev A" else "",
            storage_key=document.storage_key,
            original_filename=document.original_filename,
            file_size_bytes=document.file_size_bytes,
        )
    )

    storage_key, original_filename, size_bytes = save_upload(file, "documents")
    new_revision = _next_revision_label(document.revision)

    document.revision = new_revision
    document.uploaded_by = user_id
    document.upload_date = date.today()
    document.storage_key = storage_key
    document.original_filename = original_filename
    document.file_size_bytes = size_bytes

    new_version = DocumentVersion(
        document_id=document.id, revision=new_revision, uploaded_by=user_id, upload_date=date.today(),
        notes=notes, storage_key=storage_key, original_filename=original_filename, file_size_bytes=size_bytes,
    )
    db.add(new_version)

    audit_service.log_event(
        db, ENTITY_TYPE, document.id, "New revision uploaded", user_id, new_value=new_revision
    )
    db.commit()
    db.refresh(new_version)
    return new_version


def get_download_target(db: Session, document_no: str):
    document = get_document(db, document_no)
    return resolve_path(document.storage_key), document.original_filename


def get_ai_review(db: Session, document_id: int) -> DocumentAIReview | None:
    return (
        db.query(DocumentAIReview)
        .filter(DocumentAIReview.document_id == document_id)
        .order_by(DocumentAIReview.id.desc())
        .first()
    )


def create_ai_review(db: Session, document_no: str, payload, user_id: int) -> DocumentAIReview:
    document = get_document(db, document_no)
    review = DocumentAIReview(
        document_id=document.id,
        summary=payload.summary,
        details=payload.details,
        confidence=payload.confidence,
        extracted_fields=[f.model_dump() for f in payload.extractedFields],
        suggestions=payload.suggestions,
        created_at=datetime.now(timezone.utc),
    )
    db.add(review)
    audit_service.log_event(db, ENTITY_TYPE, document.id, "AI review recorded", user_id)
    notification_service.create_notification(
        db, document.uploaded_by, "AI review completed",
        f"The {document.title} has been reviewed with {payload.confidence} confidence.",
        "AI", link_route_name="document-viewer", link_params={"documentId": document.document_no},
    )
    db.commit()
    db.refresh(review)
    return review


def get_audit_events(db: Session, document_no: str) -> list[dict]:
    document = get_document(db, document_no)
    return audit_service.get_history(db, ENTITY_TYPE, document.id)


def delete_document(db: Session, document_no: str, actor_id: int) -> None:
    document = get_document(db, document_no)
    audit_service.log_event(db, ENTITY_TYPE, document.id, "Document deleted", actor_id, previous_value=document.title)
    document.deleted_at = datetime.now(timezone.utc)
    db.commit()
