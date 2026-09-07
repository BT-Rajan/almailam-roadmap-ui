from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

SELECTED_PERMIT_STATUSES = ("Planned", "Eligible", "In Progress", "Complete", "Cancelled")


class ProjectSelectedPermit(Base):
    """The Permits picked for a project at setup (the New Project Wizard's
    Permits step, via PermitPickerDialog) -- one row per permit, the
    missing counterpart to ProjectSelectedActivity/
    ProjectSelectedSupervisionActivity that let Design/Supervision track
    per-project progress but Permits never had (migration 0073;
    Project.required_permit_documents was the previous, unwired attempt
    at this).

    Unlike those two snapshot tables, permit_catalog_item_id is a real
    (nullable, SET NULL) FK rather than a kept-as-is display id --
    PermitPrerequisite needs to join against the catalog to know which
    Design activities a given permit requires before it's eligible, so
    the link has to survive a later catalog rename. permit_name is still
    captured as an immutable snapshot for display, same as the other two
    tables, in case the catalog item is later renamed or removed.

    status starts "Planned" and becomes "Eligible" once every
    PermitPrerequisite for this permit is satisfied (see
    project_service._recompute_permit_eligibility), at which point
    Administrators are notified once (eligibility_notified_at guards
    against renotifying). "In Progress"/"Complete"/"Cancelled" are set
    directly by the user (close_permit_activity) -- there are no
    sub-tasks the way Design has; the actual application work happens
    against one or more linked GovernmentSubmission rows (see
    GovernmentSubmission.project_selected_permit_id)."""

    __tablename__ = "project_selected_permits"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permit_catalog_item_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("permit_catalog_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    permit_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*SELECTED_PERMIT_STATUSES, name="selected_permit_status"), nullable=False, default="Planned"
    )
    eligibility_met_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    eligibility_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
