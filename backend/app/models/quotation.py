from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

QUOTATION_STATUSES = ("Draft", "Approved", "Rejected", "Expired")


class Quotation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    quotation_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    revision: Mapped[str] = mapped_column(String(10), nullable=False, default="R0")
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    validity: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*QUOTATION_STATUSES, name="quotation_status"), nullable=False, default="Draft"
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="KWD")
    prepared_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms_and_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Recomputed from line items + discount on every write (see
    # services/quotation_service.py) -- stored rather than computed at
    # read time purely so list views can sort/filter on it without
    # joining and summing line items every time.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    # NULL while still an editable draft; set once the user clicks
    # Save as Final, after which content is locked and the document is
    # ready to print. A quotation can't leave Draft status until this
    # is set (see quotation_service.set_status).
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class QuotationRevision(Base):
    """Mirrors ContractRevision (see models/contract.py) -- one row per
    saved change to a quotation's content, written automatically by
    quotation_service (on create, and on every content-changing update),
    not just via an explicit user action."""

    __tablename__ = "quotation_revisions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[str] = mapped_column(String(10), nullable=False)
    revised_at: Mapped[date] = mapped_column(Date, nullable=False)
    changed_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class QuotationLineItem(Base):
    __tablename__ = "quotation_line_items"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
