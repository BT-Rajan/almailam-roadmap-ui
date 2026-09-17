from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
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


class ProjectDocumentRequirementFulfillment(Base):
    """Per-project checkbox state for a DocumentRequirementLink (#4/#5
    on the Design-stage tangle pass -- making the till-now purely
    informational checklist above actually count). DocumentRequirementLink
    itself is catalog-level, shared across every project that happens to
    use that Design activity/Permit/Supervision activity, so it can't
    hold "has THIS project's copy actually produced/gathered this
    document" -- that state is per project, not per catalog link, hence
    this separate table rather than a column on the link itself.

    document_id, if set, is which of this project's own ProjectDocuments
    the user pointed at as the evidence -- optional (SET NULL if that
    document is later deleted), since not every requirement maps neatly
    onto a single uploaded file, but recorded when it does for
    traceability. fulfilled_at/fulfilled_by rather than a plain boolean,
    so "checked, and by whom, and when" survives the same way every
    other status change in this app does (unchecking clears both, same
    as ProjectSelectedActivity.closed_at/closed_by on reopen)."""

    __tablename__ = "project_document_requirement_fulfillments"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "document_requirement_link_id", name="uq_project_doc_req_fulfillments_target"
        ),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_requirement_link_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("document_requirement_links.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_documents.id", ondelete="SET NULL"), nullable=True
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fulfilled_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
