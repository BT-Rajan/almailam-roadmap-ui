from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_EXECUTION_STEP_STATUSES = ("Pending", "Completed", "Waived")


class ExecutionStepTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """Admin-configurable master list of the linear, tangible-act
    execution steps every project follows -- e.g. "Architectural
    drawings completed", in order, each carrying a weight_percentage
    that (across the whole template) should sum to 100.

    Every project gets its own independent COPY of this list at
    creation time (see ProjectExecutionStep) rather than a live
    reference to these rows. That's deliberate: editing a step's name
    or weight here only affects projects created afterward -- an
    already-in-progress project's completion percentage stays stable
    rather than silently shifting under it every time admin tunes the
    template. "No rework or doubling entry" -- this is the one place
    the steps and their weights are actually defined; nothing else
    hand-maintains a second copy of this list.

    One global template for now, not one per service -- the source
    process this digitizes (First Meeting through Lighting drawings)
    is a single, specific procedure, not one that currently varies by
    project type. Extending to multiple templates later is a natural
    fit for this same shape if that's ever needed, without disturbing
    projects already running against this one.

    stage_key groups each step under one of the 5 Project Approval
    Process stages (see approval_process.py) it feeds into -- e.g. the
    architectural/3D design steps fall under "architectural_approval",
    the structural/interior/MEP drawing steps fall under
    "submit_baladia_kfd" since they're submitted together as the full
    technical package. "Permit Approved" (the final approval stage) has
    no execution steps of its own -- it's a pure external gate.
    is_optional marks a step that a client's specific requirements can
    waive (see ProjectExecutionStep.status) rather than every step
    being mandatory for every project.
    """

    __tablename__ = "execution_step_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(40), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProjectExecutionStep(Base, TimestampMixin):
    """One project's own snapshot of the execution-step checklist, copied
    from ExecutionStepTemplate the moment the project is created.

    Linear by design: a step can only be marked complete once every
    step before it (by sequence_number) is already Completed or
    Waived, and can only be un-marked if it's the most recently
    resolved one -- undoing a mistake is allowed, skipping ahead or
    leaving a gap in the middle is not. See
    execution_step_service.complete_step / uncomplete_step.

    Waived (only reachable from Pending, only when is_optional is
    true) covers a step a client's specific requirements don't call
    for -- e.g. no false ceiling wanted, so "False ceiling drawings
    completed" is waived rather than left permanently Pending. A
    waived step counts toward progress exactly like a completed one
    (see execution_step_service._recompute_progress) and unblocks the
    steps after it, but keeps its own audit trail (waived_at/by/reason)
    separate from completed_at/by so "why is this step done" stays
    answerable.

    Project.progress is computed as the sum of resolved (Completed or
    Waived) steps' weight_percentage (see
    execution_step_service.recompute_progress), not typed in by hand
    -- this is what "clean, measurable progress" means in practice: a
    number nobody had to estimate.
    """

    __tablename__ = "project_execution_steps"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(40), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_EXECUTION_STEP_STATUSES, name="project_execution_step_status"),
        nullable=False,
        default="Pending",
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    waived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    waived_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    waived_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
