from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK


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
    is_optional flags a step that doesn't apply to every project (e.g.
    a client who doesn't want a false ceiling has no real use for
    "False ceiling drawings completed") -- purely informational since
    migration 0022: nothing gates on it, a PM can leave an
    inapplicable step at 0% (with a remark saying why) same as any
    other step.
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

    Since migration 0022: each step carries its own free-standing
    0-100 completion_percentage (see execution_step_service.
    set_step_progress) -- not a linear Pending/Completed/Waived status.
    A step can be set to any percentage independently of every other
    step; nothing here enforces an order between them.

    Project.progress is computed as the weight_percentage-weighted sum
    of every step's completion_percentage (see
    execution_step_service._recompute_progress), not typed in by hand
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
    completion_percentage: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
