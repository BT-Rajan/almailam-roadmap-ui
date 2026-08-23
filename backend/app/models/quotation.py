from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

QUOTATION_STATUSES = ("Draft", "Sent", "Approved", "Rejected", "Expired")

# Selectable pre-written quotation letters (see docs on the two source
# .docx templates this was built from). None means the original generic
# itemised-pricing layout, kept for any quotation created before these
# templates existed or where a lettered format doesn't apply.
QUOTATION_TEMPLATE_KEYS = ("design-and-permits", "supervision")
FEE_FREQUENCIES = ("Lump Sum", "Monthly")


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
    tax_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms_and_conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Recomputed from line items + tax + discount on every write (see
    # services/quotation_service.py) -- stored rather than computed at
    # read time purely so list views can sort/filter on it without
    # joining and summing line items every time.
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # --- Lettered-template fields -------------------------------------
    # Which pre-written letter this quotation is rendered into, if any.
    # Everything below is populated only when template_key is set; it's
    # free text specific to *this* document (not derived from Client or
    # Project) so it needs to live here to stay directly editable per
    # the "fields that don't come from DB stay editable" requirement.
    template_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # The addressee line ("السيد/ ..."), prefillable from the client's
    # contact person but kept free text since a quotation letter's
    # addressee can differ from the client record (a different signatory
    # for this particular letter).
    client_representative: Mapped[str | None] = mapped_column(String(150), nullable=True)
    subject_line: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # The plot/parcel/area line ("قسيمة رقم ... – قطعة ... - منطقة ...").
    project_reference: Mapped[str | None] = mapped_column(String(300), nullable=True)
    fee_frequency: Mapped[str] = mapped_column(
        Enum(*FEE_FREQUENCIES, name="quotation_fee_frequency"), nullable=False, default="Lump Sum"
    )
    # Bulleted scope-of-work lines, grouped under the template's phase
    # headings (e.g. "Phase 1 (Design)" / "Phase 2 (Licensing)") -- the
    # heading text itself lives in the template component since it's
    # fixed boilerplate, this list is just the bullet content per phase.
    scope_items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Payment milestone lines ("25% on contract signing", ...).
    payment_terms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # NULL while the letter is still an editable draft; set once the
    # user clicks Save/Finalize, after which the free-text fields above
    # are locked and the document is ready to print.
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class QuotationLineItem(Base):
    __tablename__ = "quotation_line_items"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
