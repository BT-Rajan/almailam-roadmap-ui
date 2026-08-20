from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_EXECUTION_STEP_STATUSES = ("Pending", "Completed")


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
    """

    __tablename__ = "execution_step_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)


class ProjectExecutionStep(Base, TimestampMixin):
    """One project's own snapshot of the execution-step checklist, copied
    from ExecutionStepTemplate the moment the project is created.

    Linear by design: a step can only be marked complete once every
    step before it (by sequence_number) already is, and can only be
    un-marked if it's the most recently completed one -- undoing a
    mistake is allowed, skipping ahead or leaving a gap in the middle
    is not. See execution_step_service.complete_step /
    uncomplete_last_step.

    Project.progress is computed as the sum of completed steps'
    weight_percentage (see execution_step_service.recompute_progress),
    not typed in by hand -- this is what "clean, measurable progress"
    means in practice: a number nobody had to estimate.
    """

    __tablename__ = "project_execution_steps"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_EXECUTION_STEP_STATUSES, name="project_execution_step_status"),
        nullable=False,
        default="Pending",
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
