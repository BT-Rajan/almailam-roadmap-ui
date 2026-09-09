from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

TASK_PRIORITIES = ("High", "Medium", "Low")
TASK_SEVERITIES = ("Critical", "Major", "Minor")
# 'Preset' (migration 0088) is the initial status for a system-generated
# service task (see project_service._create_service_tasks) -- distinct
# from 'Pending', a manually-created task's own default. Graduates to
# 'Pending' the moment anything about it is touched (see
# task_service.update_task); the UI treats a task still sitting in
# 'Preset' as a flagged, needs-review item.
TASK_STATUSES = ("Preset", "Pending", "In Progress", "Completed")


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
    # Same idea as selected_activity_id above, for Permit/Supervision
    # tracks (migration 0088) -- Permits and Supervision activities used
    # to have no sub-tasks at all (closed directly by the user, see
    # project_service.set_permit_status/set_supervision_status); now
    # every one of the three tracks gets auto-generated tasks the moment
    # the project leaves Contract (_create_service_tasks), and closing
    # the last task linked to a permit/supervision row auto-closes it
    # too, mirroring maybe_auto_close_design_activity exactly (see
    # project_service.maybe_auto_close_permit/
    # maybe_auto_close_supervision_activity).
    selected_permit_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("project_selected_permits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    selected_supervision_activity_id: Mapped[int | None] = mapped_column(
        BigPK,
        ForeignKey("project_selected_supervision_activities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    assigned_to: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum(*TASK_PRIORITIES, name="task_priority"), nullable=False, default="Medium"
    )
    severity: Mapped[str] = mapped_column(
        Enum(*TASK_SEVERITIES, name="task_severity"), nullable=False, default="Minor"
    )
    # Optional (migration 0088) -- when set, this is when work on the
    # task is meant to begin, alongside due_date/due_time below (when
    # it's meant to be done by). Auto-created service tasks always set
    # this to the project's own start_date; a manually-created task can
    # leave it blank, same as before this column existed.
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*TASK_STATUSES, name="task_status"), nullable=False, default="Pending"
    )
