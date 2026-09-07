from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

TASK_PRIORITIES = ("High", "Medium", "Low")
TASK_SEVERITIES = ("Critical", "Major", "Minor")
TASK_STATUSES = ("Pending", "In Progress", "Completed")


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    task_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Optional link to the Design activity this task belongs to
    # (migration 0073) -- only Design uses this; Permit/Supervision
    # tracks have no sub-tasks (see ProjectSelectedPermit/
    # ProjectSelectedSupervisionActivity, both closed directly by the
    # user). A task with no link here is just a generic to-do, same as
    # every task before this column existed. See project_service.
    # _maybe_auto_close_design_activity for what closing the last
    # linked task does.
    selected_activity_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_selected_activities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    assigned_to: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum(*TASK_PRIORITIES, name="task_priority"), nullable=False, default="Medium"
    )
    severity: Mapped[str] = mapped_column(
        Enum(*TASK_SEVERITIES, name="task_severity"), nullable=False, default="Minor"
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*TASK_STATUSES, name="task_status"), nullable=False, default="Pending"
    )
