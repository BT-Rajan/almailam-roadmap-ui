from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

CONTRACT_STATUSES = ("Draft", "Sent", "Signed", "Active", "Expired", "Terminated")


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    contract_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    template_name: Mapped[str] = mapped_column(String(150), nullable=False)
    revision: Mapped[str] = mapped_column(String(10), nullable=False, default="R0")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="KWD")
    contract_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    signed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*CONTRACT_STATUSES, name="contract_status"), nullable=False, default="Draft"
    )
    prepared_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    # The client's own signatory -- an external person, not a row in our
    # users table, so this stays free text rather than an FK.
    client_representative: Mapped[str] = mapped_column(String(150), nullable=False)
    scope_summary: Mapped[str] = mapped_column(Text, nullable=False)


class ContractClause(Base):
    __tablename__ = "contract_clauses"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)


class ContractRevision(Base):
    __tablename__ = "contract_revisions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[str] = mapped_column(String(10), nullable=False)
    revised_at: Mapped[date] = mapped_column(Date, nullable=False)
    changed_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
