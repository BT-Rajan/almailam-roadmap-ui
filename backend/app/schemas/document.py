from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.document import DOCUMENT_STATUSES


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class DocumentOut(BaseModel):
    id: str
    projectId: str
    title: str
    type: str
    revision: str
    stageKey: str | None
    uploadedBy: str
    uploadDate: date
    status: str
    fileSize: str | None
    originalFilename: str | None
    externalLink: str | None
    sourceFormId: str | None = None

    @staticmethod
    def from_model(document, project_no: str, uploaded_by_name: str, file_size_display: str | None) -> "DocumentOut":
        return DocumentOut(
            id=document.document_no,
            projectId=project_no,
            title=document.title,
            type=document.type,
            revision=document.revision,
            stageKey=document.stage_key,
            uploadedBy=uploaded_by_name,
            uploadDate=document.upload_date,
            status=document.status,
            fileSize=file_size_display,
            originalFilename=document.original_filename,
            externalLink=document.external_link,
            sourceFormId=f"FORM-{document.source_form_id:03d}" if document.source_form_id else None,
        )


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    # Empty string clears the stage tag (goes back to "unassigned");
    # omitted (None) leaves it untouched -- distinct meanings, see
    # document_service.update_document.
    stageKey: str | None = Field(default=None, max_length=40)
    # Same omitted-vs-empty-string convention as stageKey above --
    # empty string clears the link, omitted leaves it untouched.
    externalLink: str | None = Field(default=None, max_length=1000)
    uploadDate: date | None = None


class DocumentStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(DOCUMENT_STATUSES, "status"))


class DocumentVersionOut(BaseModel):
    id: str
    documentId: str
    revision: str
    uploadedBy: str
    uploadDate: date
    notes: str
    originalFilename: str

    @staticmethod
    def from_model(version, document_id_for_numbering: int, document_no: str, uploaded_by_name: str) -> "DocumentVersionOut":
        return DocumentVersionOut(
            # The real database id, not a synthetic "DOCV-doc-revision"
            # string -- needed so a specific version can actually be
            # downloaded (GET .../versions/{id}/download), not just
            # displayed. The old synthetic id was only ever used as a
            # Vue :key/equality check on the frontend, never parsed, so
            # this is safe to change.
            id=str(version.id),
            documentId=document_no,
            revision=version.revision,
            uploadedBy=uploaded_by_name,
            uploadDate=version.upload_date,
            notes=version.notes,
            originalFilename=version.original_filename,
        )


