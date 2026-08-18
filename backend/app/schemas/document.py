from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.document import AI_CONFIDENCE_LEVELS, DOCUMENT_STATUSES


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
    uploadedBy: str
    uploadDate: date
    status: str
    fileSize: str
    originalFilename: str

    @staticmethod
    def from_model(document, project_no: str, uploaded_by_name: str, file_size_display: str) -> "DocumentOut":
        return DocumentOut(
            id=document.document_no,
            projectId=project_no,
            title=document.title,
            type=document.type,
            revision=document.revision,
            uploadedBy=uploaded_by_name,
            uploadDate=document.upload_date,
            status=document.status,
            fileSize=file_size_display,
            originalFilename=document.original_filename,
        )


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)


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


class ExtractedFieldIn(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=500)
    confidence: str
    _check = field_validator("confidence")(_enum_validator(AI_CONFIDENCE_LEVELS, "confidence"))


class ExtractedFieldOut(BaseModel):
    label: str
    value: str
    confidence: str


class DocumentAIReviewOut(BaseModel):
    documentId: str
    summary: str
    details: str
    confidence: str
    extractedFields: list[ExtractedFieldOut]
    suggestions: list[str]

    @staticmethod
    def from_model(review, document_no: str) -> "DocumentAIReviewOut":
        return DocumentAIReviewOut(
            documentId=document_no,
            summary=review.summary,
            details=review.details,
            confidence=review.confidence,
            extractedFields=[ExtractedFieldOut(**f) for f in review.extracted_fields],
            suggestions=review.suggestions,
        )


class DocumentAIReviewCreate(BaseModel):
    summary: str = Field(min_length=1)
    details: str = Field(min_length=1)
    confidence: str
    extractedFields: list[ExtractedFieldIn] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    _check = field_validator("confidence")(_enum_validator(AI_CONFIDENCE_LEVELS, "confidence"))
