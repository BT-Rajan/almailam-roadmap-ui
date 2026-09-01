from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

SERVICE_BRANCHES = ("Design", "Supervision")


class ServiceCatalogItem(Base, TimestampMixin, SoftDeleteMixin):
    """A configurable top-level service offered by the firm (e.g.
    'Structural Engineering'). Replaces what used to be a hardcoded list
    (PROJECT_SERVICES) so admins can add/remove services without a code
    change. Name uniqueness is enforced case-insensitively in
    service_catalog_service, since 'MEP Design' and 'mep design' being
    treated as distinct would defeat the point of a duplicate check.

    branch (migration 0059) determines billing behavior: Design services
    are one-time fees; the single Supervision service's activities are
    monthly recurring fees, day-prorated for partial calendar months (see
    payment_calculations.generate_prorated_monthly_schedule)."""

    __tablename__ = "service_catalog_items"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    branch: Mapped[str] = mapped_column(
        Enum(*SERVICE_BRANCHES, name="service_catalog_branch"), nullable=False, default="Design",
    )

    activities: Mapped[list["ServiceCatalogActivity"]] = relationship(
        back_populates="service",
        order_by="ServiceCatalogActivity.id",
        cascade="all, delete-orphan",
    )


class ServiceCatalogActivity(Base):
    """A sub-service ('activity') under a service, with its own fixed
    cost -- e.g. Structural Engineering -> 'Site Inspection' at a fixed
    price. No soft-delete/timestamps here: these are simple child rows
    scoped entirely to their parent service."""

    __tablename__ = "service_catalog_activities"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service_catalog_items.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    fixed_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    service: Mapped[ServiceCatalogItem] = relationship(back_populates="activities")
