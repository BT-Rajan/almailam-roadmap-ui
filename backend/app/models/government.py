from datetime import date

from sqlalchemy import JSON, Date, Enum, ForeignKey, String, Text
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
