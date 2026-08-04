from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

DOCUMENT_TYPES = ("Drawing", "Report", "Contract", "Quotation", "Municipality Form", "Calculation Sheet")
DOCUMENT_STATUSES = ("Draft", "Under Review", "Approved", "Rejected")
AI_CONFIDENCE_LEVELS = ("high", "medium", "low")


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
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)


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


class DocumentAIReview(Base):
    __tablename__ = "document_ai_reviews"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("project_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(Enum(*AI_CONFIDENCE_LEVELS, name="ai_confidence"), nullable=False)
    extracted_fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
