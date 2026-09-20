"""Documents already on file that can satisfy a permit application's
required-documents checklist without uploading them again.

Candidates come from four places, all scoped to the application's own
project (or its client):
  project      -- a project document (Design tab / generated forms)
  client       -- a client document (Civil ID, trade licence ...)
  link         -- a project link document (Property / Government ... links)
  application  -- a file already attached to another application on the
                  same project (both seeded forms ask for architectural
                  drawings, for instance)

Attaching reuses the same stored file (or link) -- nothing is copied --
and snapshots it on the checklist row, so the entry stays valid if the
source is later replaced or removed.
"""

import re
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationAppError
from app.core.file_storage import format_file_size
from app.models.client import ClientDocument
from app.models.document import ProjectDocument, ProjectLinkDocument
from app.models.government import GovernmentSubmission, SubmissionDocument
from app.models.project import Project
from app.services import audit_service, submission_service

SOURCE_TYPES = ("project", "client", "link", "application")

_WORD = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {"the", "and", "for", "with", "owner", "copy", "document", "documents", "file", "form"}


def _keywords(text: str) -> set[str]:
    # Crude plural fold ("drawings" ~ "drawing") is enough for matching
    # checklist names against titles; this only orders the list.
    return {w.rstrip("s") for w in _WORD.findall(text.lower()) if len(w) >= 3 and w not in _STOP_WORDS}


def _is_suggested(checklist_name: str, *labels: str) -> bool:
    name_words = _keywords(checklist_name)
    if not name_words:
        return False
    label_words: set[str] = set()
    for label in labels:
        label_words |= _keywords(label or "")
    return bool(name_words & label_words)


def _candidate(
    source_type: str,
    source_id: int,
    title: str,
    category: str,
    *,
    filename: str | None,
    size_bytes: int | None,
    external_link: str | None,
    on_date: date | None,
    expiry_date: date | None,
    suggested: bool,
    from_application: str | None = None,
) -> dict:
    return {
        "sourceType": source_type,
        "sourceId": source_id,
        "title": title,
        "category": category,
        "filename": filename,
        "fileSizeLabel": format_file_size(size_bytes) if size_bytes else None,
        "externalLink": external_link,
        "onDate": on_date,
        "expiryDate": expiry_date,
        "suggested": suggested,
        "fromApplication": from_application,
    }


def list_candidates(
    db: Session,
    submission_no: str,
    document_id: int,
    *,
    include_documents: bool,
    include_client: bool,
) -> list[dict]:
    """Everything on file that could satisfy this checklist entry, the
    likeliest matches first. include_documents / include_client are the
    caller's Documents / Clients view permissions -- a source the caller
    couldn't otherwise open is never offered."""
    submission = submission_service.get_submission(db, submission_no)
    entry = submission_service._get_document(db, submission, document_id)
    project = db.query(Project).filter(Project.id == submission.project_id).first()
    candidates: list[dict] = []

    if include_documents:
        for doc in (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == submission.project_id, ProjectDocument.deleted_at.is_(None))
            .all()
        ):
            if not doc.storage_key and not doc.external_link:
                continue
            candidates.append(_candidate(
                "project", doc.id, doc.title, doc.type,
                filename=doc.original_filename if doc.storage_key else None,
                size_bytes=doc.file_size_bytes if doc.storage_key else None,
                external_link=None if doc.storage_key else doc.external_link,
                on_date=doc.upload_date, expiry_date=None,
                suggested=_is_suggested(entry.name, doc.title, doc.type),
            ))
        for link in (
            db.query(ProjectLinkDocument)
            .filter(ProjectLinkDocument.project_id == submission.project_id, ProjectLinkDocument.deleted_at.is_(None))
            .all()
        ):
            candidates.append(_candidate(
                "link", link.id, link.name, link.category,
                filename=None, size_bytes=None, external_link=link.path,
                on_date=link.added_date, expiry_date=None,
                suggested=_is_suggested(entry.name, link.name, link.category),
            ))

    if include_client and project is not None:
        for doc in (
            db.query(ClientDocument)
            .filter(ClientDocument.client_id == project.client_id, ClientDocument.deleted_at.is_(None))
            .all()
        ):
            candidates.append(_candidate(
                "client", doc.id, doc.title, doc.category,
                filename=doc.original_filename, size_bytes=doc.file_size_bytes, external_link=None,
                on_date=doc.upload_date.date() if doc.upload_date else None, expiry_date=doc.expiry_date,
                suggested=_is_suggested(entry.name, doc.title, doc.category),
            ))

    # Other applications on this project -- same name is the strongest
    # signal there is, so it always counts as suggested.
    sibling_rows = (
        db.query(SubmissionDocument, GovernmentSubmission.submission_no)
        .join(GovernmentSubmission, GovernmentSubmission.id == SubmissionDocument.submission_id)
        .filter(
            GovernmentSubmission.project_id == submission.project_id,
            GovernmentSubmission.deleted_at.is_(None),
            SubmissionDocument.id != entry.id,
        )
        .all()
    )
    for sibling, sibling_no in sibling_rows:
        if not sibling.storage_key and not sibling.external_link:
            continue
        candidates.append(_candidate(
            "application", sibling.id, sibling.name, sibling_no,
            filename=sibling.original_filename if sibling.storage_key else None,
            size_bytes=sibling.file_size_bytes if sibling.storage_key else None,
            external_link=None if sibling.storage_key else sibling.external_link,
            on_date=sibling.upload_date, expiry_date=None,
            suggested=sibling.name.strip().lower() == entry.name.strip().lower()
            or _is_suggested(entry.name, sibling.name),
            from_application=sibling_no,
        ))

    candidates.sort(key=lambda c: (not c["suggested"], -(c["onDate"].toordinal() if c["onDate"] else 0)))
    return candidates


def attach(
    db: Session,
    submission_no: str,
    document_id: int,
    source_type: str,
    source_id: int,
    user_id: int | None,
    *,
    include_documents: bool,
    include_client: bool,
) -> SubmissionDocument:
    """Points one checklist entry at a document already on file. Only
    while the application is in Prepare, like a direct upload."""
    submission = submission_service.get_submission(db, submission_no)
    if submission.stage != "Prepare":
        raise ValidationAppError("Required documents can only be updated while the application is in Prepare.")
    entry = submission_service._get_document(db, submission, document_id)
    if source_type not in SOURCE_TYPES:
        raise ValidationAppError("Unknown document source.")

    storage_key = original_filename = external_link = None
    size_bytes = None
    title = ""

    if source_type == "project":
        if not include_documents:
            raise PermissionDeniedError()
        doc = (
            db.query(ProjectDocument)
            .filter(
                ProjectDocument.id == source_id,
                ProjectDocument.project_id == submission.project_id,
                ProjectDocument.deleted_at.is_(None),
            )
            .first()
        )
        if doc is None:
            raise NotFoundError("Project document")
        title = doc.title
        if doc.storage_key:
            storage_key, original_filename, size_bytes = doc.storage_key, doc.original_filename, doc.file_size_bytes
        elif doc.external_link:
            external_link, original_filename = doc.external_link, doc.title
        else:
            raise ValidationAppError("That document has no file or link to reuse.")

    elif source_type == "link":
        if not include_documents:
            raise PermissionDeniedError()
        link = (
            db.query(ProjectLinkDocument)
            .filter(
                ProjectLinkDocument.id == source_id,
                ProjectLinkDocument.project_id == submission.project_id,
                ProjectLinkDocument.deleted_at.is_(None),
            )
            .first()
        )
        if link is None:
            raise NotFoundError("Project link document")
        title = link.name
        external_link, original_filename = link.path, link.name

    elif source_type == "client":
        if not include_client:
            raise PermissionDeniedError()
        project = db.query(Project).filter(Project.id == submission.project_id).first()
        client_doc = (
            db.query(ClientDocument)
            .filter(
                ClientDocument.id == source_id,
                ClientDocument.client_id == (project.client_id if project else -1),
                ClientDocument.deleted_at.is_(None),
            )
            .first()
        )
        if client_doc is None:
            raise NotFoundError("Client document")
        title = client_doc.title
        storage_key = client_doc.storage_key
        original_filename = client_doc.original_filename
        size_bytes = client_doc.file_size_bytes

    else:  # application
        sibling = (
            db.query(SubmissionDocument)
            .join(GovernmentSubmission, GovernmentSubmission.id == SubmissionDocument.submission_id)
            .filter(
                SubmissionDocument.id == source_id,
                GovernmentSubmission.project_id == submission.project_id,
                GovernmentSubmission.deleted_at.is_(None),
            )
            .first()
        )
        if sibling is None or sibling.id == entry.id:
            raise NotFoundError("Application document")
        if not sibling.storage_key and not sibling.external_link:
            raise ValidationAppError("That checklist entry has nothing uploaded yet.")
        title = sibling.name
        storage_key, original_filename, size_bytes = sibling.storage_key, sibling.original_filename, sibling.file_size_bytes
        external_link = sibling.external_link if not sibling.storage_key else None

    entry.storage_key = storage_key
    entry.original_filename = original_filename
    entry.file_size_bytes = size_bytes
    entry.external_link = external_link
    entry.source_type = source_type
    entry.source_id = source_id
    entry.uploaded_by = user_id
    entry.upload_date = date.today()
    if entry.status == "Pending":
        entry.status = "Uploaded"

    audit_service.log_event(
        db, submission_service.ENTITY_TYPE, submission.id, "Required document attached from documents on file",
        user_id, new_value=f"{entry.name} <- {source_type}: {title}",
    )
    db.commit()
    db.refresh(entry)
    return entry
