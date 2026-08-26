from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK


class TypeActivityCategory(Base, TimestampMixin, SoftDeleteMixin):
    """An admin-configurable engagement type (e.g. 'Design', 'Supervision')
    used at the final step of the New Project wizard: picking a category
    here is what determines which checklist of activities gets offered.
    Deliberately separate from ServiceCatalogItem (service_catalog.py) --
    a service is what the firm sells and prices per-activity; a type
    category is a *classification of the engagement itself*, and its
    activities exist to catch work that isn't already priced under the
    chosen service(s) (see TypeActivityItem's own docstring, and
    project_service.py's quotation-line-item generation, for how the two
    catalogs reconcile against each other rather than always stacking)."""

    __tablename__ = "type_activity_categories"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    activities: Mapped[list["TypeActivityItem"]] = relationship(
        back_populates="category",
        order_by="TypeActivityItem.id",
        cascade="all, delete-orphan",
    )


class TypeActivityItem(Base):
    """A checkbox-able activity under a type category, with its own
    price -- used only when the project doesn't already cover it via a
    selected service activity of the same name (case-insensitive match,
    see project_service.list_uncovered_type_activities). No soft-delete/
    timestamps, same reasoning as ServiceCatalogActivity: a simple child
    row scoped entirely to its parent category."""

    __tablename__ = "type_activity_items"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("type_activity_categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    category: Mapped[TypeActivityCategory] = relationship(back_populates="activities")
