from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK


class PermitCatalogItem(Base, TimestampMixin, SoftDeleteMixin):
    """A configurable permit an engagement may require (e.g. 'Building
    Permit'). Replaces the free-text permit search sourced from the
    government form library, so admins maintain one authoritative list
    the same way they maintain the service catalog. Flat -- unlike
    ServiceCatalogItem there's no activities sub-level, since a permit
    is picked as a whole, not broken into priced sub-items. Name
    uniqueness is enforced case-insensitively in permit_catalog_service.
    """

    __tablename__ = "permit_catalog_items"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
