from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.government import (
    AUTHORITY_CATEGORIES,
    FORM_CATEGORIES,
    FORM_LANGUAGES,
    FORM_STATUSES,
    REQUIRED_DOCUMENT_STATUSES,
    SUBMISSION_STATUSES,
)


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


# --- authorities -------------------------------------------------------


class AuthorityOut(BaseModel):
    id: str
    name: str
    category: str
    website: str
    description: str

    @staticmethod
    def from_model(authority) -> "AuthorityOut":
        return AuthorityOut(
            id=f"AUTH-{authority.id:03d}",
            name=authority.name,
            category=authority.category,
            website=authority.website,
            description=authority.description,
        )


class AuthorityIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str
    website: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)

    _check = field_validator("category")(_enum_validator(AUTHORITY_CATEGORIES, "category"))


# --- forms ---------------------------------------------------------------


class FormOut(BaseModel):
    id: str
    authorityId: str
    formCode: str
    title: str
    version: str
    language: str
    category: str
    description: str
    requiredDocuments: list[str]
    lastUpdated: date
    previewUrl: str | None
    status: str

    @staticmethod
    def from_model(form) -> "FormOut":
        return FormOut(
            id=f"FORM-{form.id:03d}",
            authorityId=f"AUTH-{form.authority_id:03d}",
            formCode=form.form_code,
            title=form.title,
            version=form.version,
            language=form.language,
            category=form.category,
            description=form.description,
            requiredDocuments=form.required_documents,
            lastUpdated=form.updated_at.date(),
            previewUrl=form.preview_url,
            status=form.status,
        )


class FormIn(BaseModel):
    authorityId: str
    formCode: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=20)
    language: str
    category: str
    description: str = Field(min_length=1)
    requiredDocuments: list[str] = Field(default_factory=list)
    previewUrl: str | None = None

    _check_language = field_validator("language")(_enum_validator(FORM_LANGUAGES, "language"))
    _check_category = field_validator("category")(_enum_validator(FORM_CATEGORIES, "category"))


class FormStatusUpdate(BaseModel):
    status: str
    _check = field_validator("status")(_enum_validator(FORM_STATUSES, "status"))


# --- submissions -----------------------------------------------------


class SubmissionDocumentOut(BaseModel):
    name: str
    status: str

    @staticmethod
    def from_model(document) -> "SubmissionDocumentOut":
        return SubmissionDocumentOut(name=document.name, status=document.status)


class SubmissionOut(BaseModel):
    id: str
    projectId: str
    authorityId: str
    formId: str
    submissionNo: str
    status: str
    submittedDate: date | None
    expectedDecisionDate: date | None
    decisionDate: date | None
    documents: list[SubmissionDocumentOut]
    notes: str | None

    @staticmethod
    def from_model(submission, project_no: str, documents: list) -> "SubmissionOut":
        return SubmissionOut(
            id=submission.submission_no,
            projectId=project_no,
            authorityId=f"AUTH-{submission.authority_id:03d}",
            formId=f"FORM-{submission.form_id:03d}",
            submissionNo=submission.submission_no,
            status=submission.status,
            submittedDate=submission.submitted_date,
            expectedDecisionDate=submission.expected_decision_date,
            decisionDate=submission.decision_date,
            documents=[SubmissionDocumentOut.from_model(d) for d in documents],
            notes=submission.notes,
        )


class SubmissionCreate(BaseModel):
    projectId: str
    authorityId: str
    formId: str
    expectedDecisionDate: date | None = None
    notes: str | None = None


class SubmissionUpdate(BaseModel):
    expectedDecisionDate: date | None = None
    notes: str | None = None
    status: str | None = None
    reason: str | None = None

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in SUBMISSION_STATUSES:
            raise ValueError(f"status must be one of {SUBMISSION_STATUSES}")
        return value


class SubmissionStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(SUBMISSION_STATUSES, "status"))


class SubmissionDocumentStatusUpdate(BaseModel):
    status: str
    _check = field_validator("status")(_enum_validator(REQUIRED_DOCUMENT_STATUSES, "status"))
