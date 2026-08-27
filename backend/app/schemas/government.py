from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.government import (
    AUTHORITY_CATEGORIES,
    FORM_CATEGORIES,
    FORM_FIELD_TYPES,
    FORM_LANGUAGES,
    FORM_STATUSES,
    GOVERNMENT_SUBMISSION_STAGE_KEYS,
    REQUIRED_DOCUMENT_STATUSES,
    RESPONSE_OUTCOMES,
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


class FormFieldIn(BaseModel):
    """Describes one {{token}} in a form's template as a dropdown or
    radio group instead of the plain text box it'd default to -- see
    GovernmentForm.fields. `options` is required (and must be
    non-empty) for 'select'/'radio', ignored for 'text'."""

    token: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=150)
    type: str
    options: list[str] = Field(default_factory=list)

    _check_type = field_validator("type")(_enum_validator(FORM_FIELD_TYPES, "field type"))

    @field_validator("options")
    @classmethod
    def check_options(cls, value: list[str], info) -> list[str]:
        field_type = info.data.get("type")
        if field_type in ("select", "radio") and len(value) == 0:
            raise ValueError("A dropdown or radio field needs at least one option.")
        return value


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
    template: str | None = None
    serviceTags: list[str] = Field(default_factory=list)
    fields: list[FormFieldIn] = Field(default_factory=list)
    sampleFileName: str | None = None

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
            template=form.template,
            serviceTags=form.service_tags or [],
            fields=form.fields or [],
            sampleFileName=form.sample_file_original_filename,
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
    template: str | None = None
    serviceTags: list[str] = Field(default_factory=list)
    fields: list[FormFieldIn] = Field(default_factory=list)

    _check_language = field_validator("language")(_enum_validator(FORM_LANGUAGES, "language"))
    _check_category = field_validator("category")(_enum_validator(FORM_CATEGORIES, "category"))


class FormFillRequest(BaseModel):
    """Fills a form's {{token}} template with real project/context data and
    saves the rendered result as a PDF Project Document (type "Government
    Agreement") -- see government_service.fill_form."""

    projectId: str
    context: dict[str, str] = Field(default_factory=dict)
    # Document title to save under; defaults to the form's own title.
    title: str | None = None


class FormRenderPdfRequest(BaseModel):
    """Renders a form's {{token}} template with the given context straight
    to PDF bytes, with nothing persisted -- no project, no Document row.
    The admin-facing counterpart to FormFillRequest above, which requires
    a project and saves the result there; this is for trying a template
    (e.g. from Administration > Government Forms) before it's ever used
    on a real project. See government_service.render_pdf."""

    context: dict[str, str] = Field(default_factory=dict)
    title: str | None = None


class FormStatusUpdate(BaseModel):
    status: str
    _check = field_validator("status")(_enum_validator(FORM_STATUSES, "status"))


# --- project form entries (Approvals & Permits) -------------------------


class ProjectFormEntryOut(BaseModel):
    id: str
    formId: str
    formCode: str
    formTitle: str
    authorityId: str
    authorityName: str
    fieldValues: dict[str, str]
    status: str
    documentId: str | None
    createdAt: datetime
    createdBy: str | None

    @staticmethod
    def from_model(entry, form, authority, document_no: str | None, created_by_name: str | None) -> "ProjectFormEntryOut":
        return ProjectFormEntryOut(
            id=f"PFE-{entry.id:04d}",
            formId=f"FORM-{form.id:03d}",
            formCode=form.form_code,
            formTitle=form.title,
            authorityId=f"AUTH-{authority.id:03d}",
            authorityName=authority.name,
            fieldValues=entry.field_values or {},
            status=entry.status,
            documentId=document_no,
            createdAt=entry.created_at,
            createdBy=created_by_name,
        )


class ProjectFormEntryCreate(BaseModel):
    formId: str
    fieldValues: dict[str, str] = Field(default_factory=dict)


class ProjectFormEntryUpdate(BaseModel):
    fieldValues: dict[str, str] = Field(default_factory=dict)


class ProjectFormEntryStatusUpdate(BaseModel):
    status: str
    _check = field_validator("status")(_enum_validator(SUBMISSION_STATUSES, "status"))


# --- submissions -----------------------------------------------------


class SubmissionDocumentOut(BaseModel):
    id: int
    name: str
    status: str
    originalFilename: str | None = None
    fileSizeLabel: str | None = None
    uploadDate: date | None = None
    uploadedBy: str | None = None

    @staticmethod
    def from_model(document, uploaded_by_name: str | None) -> "SubmissionDocumentOut":
        from app.core.file_storage import format_file_size

        return SubmissionDocumentOut(
            id=document.id,
            name=document.name,
            status=document.status,
            originalFilename=document.original_filename,
            fileSizeLabel=format_file_size(document.file_size_bytes) if document.file_size_bytes is not None else None,
            uploadDate=document.upload_date,
            uploadedBy=uploaded_by_name,
        )


class ProofOfFileOut(BaseModel):
    originalFilename: str
    fileSizeLabel: str
    uploadDate: date
    uploadedBy: str


class FollowupOut(BaseModel):
    id: str
    followupDate: date
    followupTime: str
    contactPerson: str
    notes: str | None
    createdBy: str
    createdAt: datetime

    @staticmethod
    def from_model(followup, created_by_name: str) -> "FollowupOut":
        return FollowupOut(
            id=f"FUP-{followup.id:04d}",
            followupDate=followup.followup_date,
            followupTime=followup.followup_time,
            contactPerson=followup.contact_person,
            notes=followup.notes,
            createdBy=created_by_name,
            createdAt=followup.created_at,
        )


class FollowupCreate(BaseModel):
    followupDate: date
    followupTime: str = Field(min_length=1, max_length=20)
    contactPerson: str = Field(min_length=1, max_length=150)
    notes: str | None = None


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
    allDocumentsSatisfied: bool
    proofOfSubmission: ProofOfFileOut | None = None
    proofOfResponse: ProofOfFileOut | None = None
    responseOutcome: str | None = None
    stageKey: str | None = None

    @staticmethod
    def from_model(
        submission,
        project_no: str,
        documents: list,
        document_uploader_names: dict[int, str] | None = None,
        proof_of_submission_uploader_name: str | None = None,
        proof_of_response_uploader_name: str | None = None,
    ) -> "SubmissionOut":
        document_uploader_names = document_uploader_names or {}
        all_satisfied = bool(documents) and all(d.status in ("Uploaded", "Verified") for d in documents)

        proof_of_submission = None
        if submission.proof_of_submission_storage_key:
            from app.core.file_storage import format_file_size

            proof_of_submission = ProofOfFileOut(
                originalFilename=submission.proof_of_submission_filename,
                fileSizeLabel=format_file_size(submission.proof_of_submission_size_bytes),
                uploadDate=submission.proof_of_submission_upload_date,
                uploadedBy=proof_of_submission_uploader_name or "Unknown",
            )

        proof_of_response = None
        if submission.proof_of_response_storage_key:
            from app.core.file_storage import format_file_size

            proof_of_response = ProofOfFileOut(
                originalFilename=submission.proof_of_response_filename,
                fileSizeLabel=format_file_size(submission.proof_of_response_size_bytes),
                uploadDate=submission.proof_of_response_upload_date,
                uploadedBy=proof_of_response_uploader_name or "Unknown",
            )

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
            documents=[
                SubmissionDocumentOut.from_model(d, document_uploader_names.get(d.id)) for d in documents
            ],
            notes=submission.notes,
            allDocumentsSatisfied=all_satisfied,
            proofOfSubmission=proof_of_submission,
            proofOfResponse=proof_of_response,
            responseOutcome=submission.response_outcome,
            stageKey=submission.stage_key,
        )


class SubmissionCreate(BaseModel):
    projectId: str
    authorityId: str
    formId: str
    expectedDecisionDate: date | None = None
    notes: str | None = None
    # Which of the 3 authority-facing approval-process gates this
    # submission's own approval will satisfy, if any -- see
    # GOVERNMENT_SUBMISSION_STAGE_KEYS.
    stageKey: str | None = None

    @field_validator("stageKey")
    @classmethod
    def check_stage_key(cls, value: str | None) -> str | None:
        if value is not None and value not in GOVERNMENT_SUBMISSION_STAGE_KEYS:
            raise ValueError(f"stageKey must be one of {GOVERNMENT_SUBMISSION_STAGE_KEYS}")
        return value


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


def check_response_outcome(value: str) -> str:
    return _enum_validator(RESPONSE_OUTCOMES, "outcome")(value)
