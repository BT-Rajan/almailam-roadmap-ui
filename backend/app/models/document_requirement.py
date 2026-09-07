from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

DOCUMENT_REQUIREMENT_TARGET_TYPES = ("Design", "Permit", "Supervision")


class DocumentRequirement(Base, TimestampMixin, SoftDeleteMixin):
    """A document an admin can flag as typically needed for one or more
    catalog activities (migration 0073) -- e.g. "Site Survey Report"
    might be linked to both a Design activity and a Permit. Purely
    informational/reference: nothing in this app enforces it against
    task or activity closure ("user manually manages it"), it only
    surfaces as a reference checklist on the project's tabs. Same
    shape/uniqueness convention as PermitCatalogItem -- name uniqueness
    enforced case-insensitively in the service layer."""

    __tablename__ = "document_requirements"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class DocumentRequirementLink(Base):
    """Many-to-many: which catalog activity/permit a DocumentRequirement
    applies to -- the reuse mechanism ("we might be using a single
    document for more than one activity"). target_catalog_id is not a
    real FK (it points at service_catalog_activities.id when
    target_type is 'Design' or 'Supervision', or permit_catalog_items.id
    when it's 'Permit' -- a column can't conditionally FK two different
    tables), same tradeoff HandoverChecklistItem.source_id makes below."""

    __tablename__ = "document_requirement_links"
    __table_args__ = (
        UniqueConstraint(
            "document_requirement_id", "target_type", "target_catalog_id",
            name="uq_document_requirement_links_target",
        ),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_requirement_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("document_requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(
        Enum(*DOCUMENT_REQUIREMENT_TARGET_TYPES, name="document_requirement_target_type"), nullable=False
    )
    target_catalog_id: Mapped[int] = mapped_column(BigPK, nullable=False)
