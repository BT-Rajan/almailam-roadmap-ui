from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

CONTRACT_STATUSES = ("Draft", "Sent", "Signed", "Active", "Expired", "Terminated")

# Selectable pre-written, bilingual contract letters (see the lettered
# quotation templates this shares its source documents with). None keeps
# the original free-form clause-list contract for anything not using a
# lettered format.
CONTRACT_TEMPLATE_KEYS = ("design-and-permits", "supervision")
CONTRACT_FEE_FREQUENCIES = ("Lump Sum", "Monthly")


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    contract_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # The quotation this contract was generated from. Required going
    # forward (see contract_service.create_contract, which enforces the
    # quotation is 'Approved' and finalized before allowing this to be
    # set) -- nullable only so contracts created before this rule
    # existed remain valid rows.
    quotation_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("quotations.id", ondelete="RESTRICT"), nullable=True, index=True
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

    # --- Lettered-template fields --------------------------------------
    # Which pre-written bilingual letter this contract is rendered into,
    # if any (see QUOTATION for the parallel fields and why they're free
    # text rather than derived from Client/Project).
    template_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Rendered Arabic block first, then English block, in the same
    # document -- both stored since the two aren't a mechanical
    # translation of each other once a user edits either side.
    is_bilingual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    subject_line_ar: Mapped[str | None] = mapped_column(String(300), nullable=True)
    subject_line_en: Mapped[str | None] = mapped_column(String(300), nullable=True)
    project_reference: Mapped[str | None] = mapped_column(String(300), nullable=True)
    fee_frequency: Mapped[str] = mapped_column(
        Enum(*CONTRACT_FEE_FREQUENCIES, name="contract_fee_frequency"), nullable=False, default="Lump Sum"
    )
    scope_items_ar: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    scope_items_en: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    payment_terms_ar: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    payment_terms_en: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # NULL while still an editable draft; set once the user Saves, after
    # which the free-text fields above lock and the document prints.
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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
