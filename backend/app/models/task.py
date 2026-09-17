from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

TASK_PRIORITIES = ("High", "Medium", "Low")
TASK_SEVERITIES = ("Critical", "Major", "Minor")
# A task is linked to at most one Design activity, Permit, or Supervision
# activity (see task_service.set_status) -- linked_stage_type says which
# table linked_stage_id's value refers to (project_selected_activities,
# project_selected_permits, or project_selected_supervision_activities,
# respectively). None/None is the common case: a plain, unlinked to-do.
TASK_LINKED_STAGE_TYPES = ("Design", "Permit", "Supervision")
# 'Preset' (migration 0088) is the initial status for a system-generated
# service task (see project_service._create_service_tasks) -- distinct
# from 'Pending', a manually-created task's own default. Graduates to
# 'Pending' the moment anything about it is touched (see
# task_service.update_task); the UI treats a task still sitting in
# 'Preset' as a flagged, needs-review item.
TASK_STATUSES = ("Preset", "Pending", "In Progress", "Completed")


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"
    # See migration 0091. idx_tasks_deleted_due_date backs
    # sort_and_paginate's own default sort for every Tasks list call
    # (task_service.list_tasks: `sort or "dueDate"`) -- that runs on
    # every page load, not just a filtered subset. idx_tasks_deleted_status
    # backs a project's own Tasks tab (scoped to one stage's service
    # tasks) and the Task Board's status grouping.
    __table_args__ = (
        Index("idx_tasks_deleted_due_date", "deleted_at", "due_date"),
        Index("idx_tasks_deleted_status", "deleted_at", "status"),
        Index("idx_tasks_linked_stage", "linked_stage_type", "linked_stage_id"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    task_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Optional link to the Design activity, Permit, or Supervision
    # activity this task belongs to (migration 0104, replacing the three
    # separate nullable FKs migrations 0073/0088 had added one per track).
    # A task with both None is just a generic to-do, same as every task
    # before either column existed. No native FK constraint here -- which
    # table linked_stage_id points at depends on linked_stage_type, and
    # MySQL can't express a FK that targets one of three tables -- so
    # referential integrity is the service layer's job (see
    # project_service.get_selected_activity/get_selected_permit/
    # get_selected_supervision_activity, all of which 404 on a bad id).
    # See project_service.maybe_auto_close_design_activity/
    # maybe_auto_close_permit/maybe_auto_close_supervision_activity for
    # what closing the last linked task does.
    linked_stage_type: Mapped[str | None] = mapped_column(
        Enum(*TASK_LINKED_STAGE_TYPES, name="task_linked_stage_type"), nullable=True
    )
    linked_stage_id: Mapped[int | None] = mapped_column(BigPK, nullable=True)
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
