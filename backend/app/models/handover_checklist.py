from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

HANDOVER_CHECKLIST_SOURCE_TYPES = ("Design", "Permit", "Supervision")


class HandoverChecklistItem(Base):
    """One row per completed Design activity / Permit / Supervision
    activity on a project, generated once by
    project_service.try_complete_project when every planned item across
    all three tracks is Complete/Cancelled and payment is at 100%
    (migration 0073) -- the project's hand-over record, sent to the
    client alongside the completion email. The unique constraint below
    is what makes generation idempotent ("no repetitions") even if
    try_complete_project's checks run more than once for the same
    project.

    source_id is not a real FK -- like DocumentRequirementLink.
    target_catalog_id, it points at whichever table source_type names
    (project_selected_activities / project_selected_permits /
    project_selected_supervision_activities), and a column can't
    conditionally FK three different tables."""

    __tablename__ = "handover_checklist_items"
    __table_args__ = (
        UniqueConstraint("project_id", "source_type", "source_id", name="uq_handover_checklist_items_source"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        Enum(*HANDOVER_CHECKLIST_SOURCE_TYPES, name="handover_checklist_source_type"), nullable=False
    )
    source_id: Mapped[int] = mapped_column(BigPK, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
