from datetime import date, datetime

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

DOCUMENT_TYPES = (
    "Drawing", "Report", "Contract", "Quotation", "Municipality Form", "Calculation Sheet",
    # A filled-in government form/agreement generated from a
    # GovernmentForm template (see government_service.fill_form) and
    # saved as a real PDF -- distinct from "Municipality Form" (a
    # manually uploaded scan/file with no generation involved).
    "Government Agreement",
)
DOCUMENT_STATUSES = ("Draft", "Under Review", "Approved", "Rejected")

# The three project-level categories that are added as a link/path to a file
# stored elsewhere, rather than uploaded through the app -- "Customer ID"
# documents are a fourth category shown alongside these in the Documents
# tab, but those are read-only, sourced from the client's own onboarding
# documents (see ClientDocument / client_documents), not stored here.
PROJECT_LINK_DOCUMENT_CATEGORIES = ("Property", "Government", "Others", "Project Closure")


class ProjectDocument(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(Enum(*DOCUMENT_TYPES, name="document_type"), nullable=False)
    revision: Mapped[str] = mapped_column(String(10), nullable=False, default="Rev A")
    uploaded_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    upload_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*DOCUMENT_STATUSES, name="document_status"), nullable=False, default="Draft"
    )
    # All three nullable -- a row can be a plain external link with no
    # uploaded file at all (see external_link below), an uploaded file
    # with no link, or both; create_document requires at least one of
    # the two at the application layer, not here.
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # A link to a document that lives outside the app (a shared drive,
    # cloud folder, etc.) -- same idea as ProjectLinkDocument, but on
    # this model so the Design tab's list can mix uploaded files and
    # external links in one CRUD table.
    external_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Which GovernmentForm this document was generated from (see
    # government_service.fill_form) -- NULL for every document that
    # isn't a generated "Government Agreement" (an upload, a contract
    # PDF, etc). Lets the Required Documents checklist (see
    # ProjectOverviewTab.vue) check "has this specific form been filled
    # for this project" by a real join instead of guessing from the
    # document's title.
    source_form_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("government_forms.id", ondelete="SET NULL"), nullable=True
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("project_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[str] = mapped_column(String(10), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    upload_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)


class ProjectLinkDocument(Base, TimestampMixin, SoftDeleteMixin):
    """A document that lives outside the app (a shared drive, a government
    portal, a scanned copy on the office server, etc.) -- only its name,
    category, and a path/link back to it are recorded here. Unlike
    ProjectDocument above, there is no file storage involved: nothing is
    uploaded or downloaded through the backend, "download" on the frontend
    just opens `path`."""

    __tablename__ = "project_link_documents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    link_document_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        Enum(*PROJECT_LINK_DOCUMENT_CATEGORIES, name="project_link_document_category"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    added_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    added_date: Mapped[date] = mapped_column(Date, nullable=False)


