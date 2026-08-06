from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

TIMELINE_EVENT_TYPES = ("stage", "document", "quotation", "submission", "milestone", "task", "note")
TIMELINE_EVENT_STATUSES = ("completed", "in-progress", "upcoming")


class ProjectTimelineEvent(Base, TimestampMixin):
    __tablename__ = "project_timeline_events"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(Enum(*TIMELINE_EVENT_TYPES, name="timeline_event_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*TIMELINE_EVENT_STATUSES, name="timeline_event_status"), nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
