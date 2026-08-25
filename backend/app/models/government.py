from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

AUTHORITY_CATEGORIES = ("Municipality", "Fire Department", "Electricity", "Water", "Environment")
FORM_CATEGORIES = (
    "Building Permit",
    "Occupancy Certificate",
    "Fire Safety Approval",
    "Utility Connection",
    "Environmental Clearance",
    "Business License",
)
FORM_LANGUAGES = ("English", "Arabic", "English / Arabic")
FORM_STATUSES = ("Active", "Archived")
SUBMISSION_STATUSES = ("Draft", "Submitted", "Under Review", "Comments Received", "Approved", "Rejected", "Withdrawn")
REQUIRED_DOCUMENT_STATUSES = ("Pending", "Uploaded", "Verified")
# Outcome recorded against the "proof of response" upload -- kept as its
# own field (rather than inferred from submission.status) so the UI can
# gate the "Mark Complete" action on an explicit Approved/Rejected call,
# independent of exactly which status the submission is sitting in.
RESPONSE_OUTCOMES = ("Approved", "Rejected")
# Which of the project's 5 Project Approval Process gates (see
# approval_process.py) this submission's own approval satisfies --
# only the 3 that represent an actual government authority's sign-off,
# not "Documents Signed" (a contract milestone) or "Architectural
# Design Approved by Client" (the client's own sign-off, not an
# authority's). Optional: a submission not tagged to one of these
# doesn't drive any project-level gate on its own.
GOVERNMENT_SUBMISSION_STAGE_KEYS = ("mew_approval", "submit_baladia_kfd", "permit_approved")


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


class GovernmentSubmission(Base, TimestampMixin, SoftDeleteMixin):
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
    status: Mapped[str] = mapped_column(
        Enum(*SUBMISSION_STATUSES, name="government_submission_status"), nullable=False, default="Draft"
    )
    submitted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # See GOVERNMENT_SUBMISSION_STAGE_KEYS above -- set at creation,
    # optional. Once this submission reaches "Approved", submission_
    # service.set_status marks the matching ProjectApprovalStep
    # complete and tries the project's own stage auto-advance, the same
    # way a stage-gate document upload already does.
    stage_key: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Proof of submission -- uploaded once every required document is
    # Uploaded/Verified, gates the Draft -> Submitted transition (see
    # submission_service.upload_proof_of_submission).
    proof_of_submission_storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    proof_of_submission_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_of_submission_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    proof_of_submission_uploaded_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    proof_of_submission_upload_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Proof of the government's response -- uploaded once a decision comes
    # back; response_outcome drives whether "Mark Complete" is available.
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
    """A log entry recording a follow-up call/visit made to the
    authority while a submission is awaiting a decision -- who checked,
    and when. Purely additive (no edit/delete from the UI), same idea as
    audit_log: an append-only trail, not a mutable field on the
    submission itself."""

    __tablename__ = "submission_followups"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("government_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    followup_date: Mapped[date] = mapped_column(Date, nullable=False)
    followup_time: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(150), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
