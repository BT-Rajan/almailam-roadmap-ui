from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.service_catalog import ServiceCatalogActivity
from app.models.user import BigPK


class PermitPrerequisite(Base):
    """Admin-configured (migration 0073): a Permit becomes eligible to
    start (see ProjectSelectedPermit.status,
    project_service._recompute_permit_eligibility) only once every
    Design activity listed here for its permit_catalog_item_id is
    Complete on the project. Both sides reference the catalog, not a
    project instance -- this is configuration ("Building Permit needs
    Foundation Design done first"), evaluated per-project at runtime.
    No name/timestamps -- a plain admin-managed join, same minimalism as
    ServiceCatalogActivity's own child rows."""

    __tablename__ = "permit_prerequisites"
    __table_args__ = (
        UniqueConstraint("permit_catalog_item_id", "design_activity_id", name="uq_permit_prerequisites_pair"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    permit_catalog_item_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("permit_catalog_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    design_activity_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("service_catalog_activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Read-only convenience for PermitPrerequisiteOut.from_model -- no
    # back_populates, ServiceCatalogActivity doesn't need to know about
    # prerequisite rows that reference it.
    design_activity: Mapped[ServiceCatalogActivity] = relationship(foreign_keys=[design_activity_id])


class SupervisionPrerequisite(Base):
    """Same shape and purpose as PermitPrerequisite, for a Supervision
    catalog activity instead of a permit: supervision_activity_id and
    design_activity_id are both service_catalog_activities.id rows (the
    Supervision branch and the Design branch respectively) -- kept as a
    separate concrete table rather than one polymorphic table sharing
    PermitPrerequisite's shape, matching how ProjectSelectedActivity/
    ProjectSelectedSupervisionActivity are already two separate concrete
    tables in this codebase rather than one generalized one."""

    __tablename__ = "supervision_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "supervision_activity_id", "design_activity_id", name="uq_supervision_prerequisites_pair"
        ),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    supervision_activity_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("service_catalog_activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    design_activity_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("service_catalog_activities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Read-only convenience for SupervisionPrerequisiteOut.from_model --
    # no back_populates, same reasoning as PermitPrerequisite.design_activity.
    design_activity: Mapped[ServiceCatalogActivity] = relationship(foreign_keys=[design_activity_id])
