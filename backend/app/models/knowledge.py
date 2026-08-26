from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, CHAR, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

KNOWLEDGE_CONTENT_TYPES = ("pdf", "docx", "txt")


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Full extracted plain text (capped at ingest time to
    # AIConfiguration.kb_max_document_chars) -- this, not the original
    # file, is what grounds every Q&A answer.
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extraction_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extraction_error: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    uploaded_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class KnowledgeQACacheEntry(Base):
    __tablename__ = "knowledge_qa_cache"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    scope_key: Mapped[str] = mapped_column(String(64), nullable=False)
    question_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_document_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
