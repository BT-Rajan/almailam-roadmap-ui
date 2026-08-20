from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_APPROVAL_STEP_STATUSES = ("Pending", "Completed")


class ApprovalProcessTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """The 5-step Project Approval Process (Documents Signed -> MEW
    Approval -> Architectural Design Approved by Client -> Submit to
    Baladia or KFD -> Permit Approved), seeded once below and NOT yet
    exposed through an admin editing UI -- this is deliberately a
    separate, standalone trial, plugged in as new rather than replacing
    or touching the existing 9-stage current_stage/PROJECT_STAGE_
    ALLOWED_TRANSITIONS system in any way. Whether this eventually
    merges into that system, replaces part of it, or stays independent
    is an open decision pending client consultation -- keeping this
    completely decoupled (own tables, own service, own API, own modal
    UI, zero shared code with the stage system) means that decision can
    still go any direction without this trial having entangled itself
    with what already works.

    A template table exists (rather than hardcoding the 5 steps
    directly into each project) so admin-editability can be added later
    as a small, additive change if this trial is kept -- without
    needing another migration to introduce the concept from scratch.
    """

    __tablename__ = "approval_process_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)


class ProjectApprovalStep(Base, TimestampMixin):
    """One project's own snapshot of the approval process, copied from
    ApprovalProcessTemplate at creation time -- same snapshot-not-live-
    reference reasoning as ProjectExecutionStep. Linear: a step can
    only be completed once every step before it already is, and can
    only be un-completed if it's the most recently completed one.

    Deliberately does not touch projects.progress or projects.
    current_stage -- this tracks its own, separate notion of progress
    through the approval process, and doesn't feed into or read from
    either of those existing fields.
    """

    __tablename__ = "project_approval_steps"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_APPROVAL_STEP_STATUSES, name="project_approval_step_status"),
        nullable=False,
        default="Pending",
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
