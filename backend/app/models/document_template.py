from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

DOCUMENT_TEMPLATE_TYPES = ("Quotation", "Contract")
DOCUMENT_TEMPLATE_LANGUAGES = ("English", "Arabic")


class DocumentTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """An admin-uploaded .docx template, merged with live project data to
    produce the actual downloadable Quotation/Contract document (see
    document_template_service.render_quotation_document/
    render_contract_document). is_default is exclusive per
    (document_type, language) -- migration 0064 lets each document_type
    carry two defaults side by side, one per language, rather than a
    single shared one -- enforced in document_template_service.
    set_default -- MySQL has no partial/filtered unique index to express
    that as a DB constraint."""

    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_type: Mapped[str] = mapped_column(
        Enum(*DOCUMENT_TEMPLATE_TYPES, name="document_template_type"), nullable=False
    )
    # Drives both which default this template can be (see set_default)
    # and, at render time, the merged PDF's text direction/font (see
    # document_template_service._docx_to_pdf) -- an English template no
    # longer gets force-rendered right-to-left with an Arabic font just
    # because that used to be the only style _docx_to_pdf knew.
    language: Mapped[str] = mapped_column(
        Enum(*DOCUMENT_TEMPLATE_LANGUAGES, name="document_template_language"), nullable=False, default="English"
    )
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uploaded_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
