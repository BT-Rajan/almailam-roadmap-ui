from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

FORM_FIELD_TYPES = ("text", "select", "radio")

AUTHORITY_CATEGORIES = ("Municipality", "Fire Department", "Electricity", "Water", "Environment")
FORM_CATEGORIES = (
    "Building Permit",
    "Occupancy Certificate",
    "Fire Safety Approval",
    "Utility Connection",
    "Environmental Clearance",
    "Business License",
    "Agreement",
    "Legal Undertaking",
)
FORM_LANGUAGES = ("English", "Arabic", "English / Arabic")
FORM_STATUSES = ("Active", "Archived")
SUBMISSION_STAGES = ("Prepare", "Apply", "Track", "Close")
# ProjectFormEntry's own status lifecycle -- unrelated to
# SUBMISSION_STAGES above (this is "is this one filled-in form done,"
# not "where is this permit application"), kept as the exact vocabulary
# the old shared SUBMISSION_STATUSES enum used before this became its
# own constant, since ProjectFormEntry never needed the Permit
# Application rework and nothing about its own lifecycle changed.
PROJECT_FORM_ENTRY_STATUSES = ("Draft", "Submitted", "Under Review", "Comments Received", "Approved", "Rejected", "Withdrawn")
REQUIRED_DOCUMENT_STATUSES = ("Pending", "Uploaded", "Verified")
# Outcome recorded when an application reaches Close -- kept as its own
# field (rather than inferred from the stage alone) since Close is a
# single terminal stage but needs to say *how* it ended. "No Response"
# covers a follow-up made after the authority's own response window
# closed with nothing back -- still a real outcome worth recording
# (with its own proof, e.g. a follow-up acknowledgement). "Withdrawn"
# covers staff pulling the application before a decision came back --
# there's no separate stage for it anymore (see
# core/status_transitions.py's SUBMISSION_ALLOWED_TRANSITIONS), just
# this outcome recorded against whichever stage it was withdrawn from.
RESPONSE_OUTCOMES = ("Approved", "Rejected", "No Response", "Withdrawn")


class GovernmentAuthority(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "government_authorities"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(Enum(*AUTHORITY_CATEGORIES, name="authority_category"), nullable=False)
    website: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class GovernmentForm(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "government_forms"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    authority_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_authorities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    form_code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(Enum(*FORM_LANGUAGES, name="form_language"), nullable=False)
    category: Mapped[str] = mapped_column(Enum(*FORM_CATEGORIES, name="form_category"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_documents: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preview_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(*FORM_STATUSES, name="form_status"), nullable=False, default="Active"
    )
    # Fillable body, written with {{token}} merge fields (see
    # app.services.pdf_render.render_template / src/utils/
    # governmentFormHelpers.ts's identical client-side renderer). NULL for
    # a form that's just a reference/PDF sample with nothing to fill in.
    template: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Service Catalog service names this form applies to -- matched
    # against Project.service to decide which forms to suggest for a
    # project (see governmentFormHelpers.formMatchesProjectService).
    service_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Which {{token}}s in `template` get a dropdown or radio group instead
    # of a plain text box when a project fills this form in -- a list of
    # {token, label, type, options}, type one of FORM_FIELD_TYPES. A
    # token used in the template but not listed here just falls back to
    # a plain text field (see ProjectFormEntryDialog.vue) -- this is
    # additive, not a replacement for the template.
    fields: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # An uploaded reference copy of the real government form (e.g. the
    # blank official PDF) admin can check the template/fields against
    # while building them -- not parsed, purely a reference attachment.
    sample_file_storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    sample_file_original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class GovernmentSubmission(Base, TimestampMixin, SoftDeleteMixin):
    """A permit application's own workspace -- one row per application,
    walking through 4 stages (SUBMISSION_STAGES): Prepare (pick the
    authority/form this application is for, fill the form in via
    ProjectFormEntry, get the required-documents checklist ready) ->
    Apply (file it, record the authority's acknowledgement) -> Track
    (record follow-ups made with the authority while it's under review --
    including any document they asked for, which used to be its own
    "Update" stage, merged into Track by migration 0108) -> Close (the
    final outcome, permit/decision document, and closing notes). See core/status_transitions.py's
    SUBMISSION_ALLOWED_TRANSITIONS for the full stage graph and
    submission_service.py for the one action per transition.

    Named GovernmentSubmission/government_submissions still (not
    renamed to PermitApplication at the table/class level) to avoid
    churning every existing FK and import across the codebase for a
    rename that's purely cosmetic -- the frontend presents this as
    "Permit Application" regardless of what the Python class is called.
    """

    __tablename__ = "government_submissions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    submission_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    authority_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_authorities.id", ondelete="RESTRICT"), nullable=False
    )
    form_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_forms.id", ondelete="RESTRICT"), nullable=False
    )
    # Which planned permit (migration 0073) this application is
    # fulfilling -- optional, since a submission can still be created
    # ad hoc against an authority/form with no ProjectSelectedPermit
    # behind it, same as today. When set, this is what
    # project_service.set_permit_status's caller uses to find the
    # application(s) filed against a given planned permit -- staff still
    # close the permit itself by hand there, independent of this
    # application's own stage (see ProjectSelectedPermit's docstring).
    project_selected_permit_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_selected_permits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage: Mapped[str] = mapped_column(
        Enum(*SUBMISSION_STAGES, name="government_submission_stage"), nullable=False, default="Prepare"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Prepare -----------------------------------------------------
    # Set once every required document (see SubmissionDocument below) is
    # Uploaded/Verified and staff explicitly confirm it -- see
    # submission_service.confirm_readiness. Gates Prepare -> Apply the
    # same way proof-of-submission's checklist gate always has.
    readiness_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    readiness_confirmed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # --- Apply ---------------------------------------------------------
    # The authority's acknowledgement of receipt -- filed together in one
    # action (submission_service.record_acknowledgement), which is also
    # what moves the application from Apply into Track.
    acknowledgement_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    submitted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # The acknowledgement upload itself -- named proof_of_submission_*
    # rather than acknowledgement_* purely to keep the column names
    # stable across the Government Submission -> Permit Application
    # rename; it's presented to the user as "Application Acknowledgement".
    proof_of_submission_storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    proof_of_submission_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_submission_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proof_of_submission_uploaded_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    proof_of_submission_upload_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Close -----------------------------------------------------
    # The issued permit or the authority's decision letter, whichever
    # applies -- same field regardless of outcome, named proof_of_response_*
    # for the same column-stability reason as above; presented to the
    # user as "Permit / Decision Document". Optional: a Withdrawn/No
    # Response close often has nothing to attach.
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    proof_of_response_storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    proof_of_response_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_response_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proof_of_response_uploaded_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    proof_of_response_upload_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    response_outcome: Mapped[str | None] = mapped_column(
        Enum(*RESPONSE_OUTCOMES, name="submission_response_outcome"), nullable=True
    )
    closing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SubmissionDocument(Base):
    __tablename__ = "submission_documents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*REQUIRED_DOCUMENT_STATUSES, name="required_document_status"),
        nullable=False,
        default="Pending",
    )
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    upload_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class SubmissionFollowup(Base):
    """A log entry recording a follow-up made with the authority while an
    application is in Track (SUBMISSION_STAGES) -- who checked, when,
    and what came of it, plus an optional document (an additional
    document the authority asked for, or an updated version of one
    already sent). Purely additive (no edit/delete from the UI), same
    idea as audit_log: an append-only trail, not a mutable field on the
    application itself.
    """

    __tablename__ = "submission_followups"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    followup_date: Mapped[date] = mapped_column(Date, nullable=False)
    followup_time: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(150), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ProjectFormEntry(Base, TimestampMixin):
    """One government form, filled in and saved for one project -- the
    Permit Application workspace's Prepare stage uses this to fill in
    the actual form for whichever authority/type of approval was
    selected, organized by the form's authority (MEW/KFD/Baladia/...).
    Distinct from GovernmentSubmission above: an application tracks the
    back-and-forth of filing something WITH an authority and waiting on
    a decision; this is just "this project has this one form filled
    in," with its own status lifecycle (PROJECT_FORM_ENTRY_STATUSES,
    kept separate from SUBMISSION_STAGES above since the two track
    genuinely different things now).

    Saving (see project_form_service.create_project_form_entry) does
    two things in one action, per how staff actually work: persists
    field_values here AND renders the same data to a PDF saved as a
    Project Document (document_id) -- there's no separate "save the
    data" vs "generate the PDF" step. A project can only have one entry
    per form (see the unique constraint below) -- refilling means
    editing this same entry, not creating a second one.
    """

    __tablename__ = "project_form_entries"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    form_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_forms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Keyed by the template's {{token}} names -- see GovernmentForm.fields
    # for which of them are dropdowns/radio groups vs. plain text.
    field_values: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_FORM_ENTRY_STATUSES, name="project_form_entry_status"), nullable=False, default="Draft"
    )
    # The generated PDF -- always set once this row exists (see the
    # class docstring); nullable only because the FK itself can't be
    # NOT NULL until the row and the document are both flushed in the
    # same transaction. Download/Print are only ever offered once this
    # is set, which in practice is from the moment the row is visible
    # at all.
    document_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_documents.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)

    __table_args__ = (UniqueConstraint("project_id", "form_id", name="uq_project_form_entries_project_form"),)
