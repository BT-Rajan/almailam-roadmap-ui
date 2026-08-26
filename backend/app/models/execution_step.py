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

    stage_key groups each step under one of the 7 project workflow
    stages it happens during (see project.py's WORKFLOW_STAGES and
    execution_step_service.STAGE_KEYS) -- e.g. "Client Civil ID
    collected" during Contract, "Architectural drawings completed"
    during Design (migration 0029 repointed this column to workflow
    stages; it used to hold one of the 5 ApprovalProcessTemplate gate
    keys instead). Despite ApprovalProcessTemplate also having a
    stage_key column, the two are disjoint concepts on two genuinely
    independent tracks -- see that model's own docstring. A handful of
    specific steps that duplicate a specific gate closing (or a
    Quotation/Contract being created) auto-complete when that gate
    closes instead of making staff tick the same fact twice -- see
    execution_step_service.try_auto_fill and its _AUTO_FILL_TRIGGERS
    table, keyed by sequence_number, not stage_key.
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
    # Project-local, unlike is_optional (copied from the template and
    # shared across every project's snapshot): drops this one activity,
    # for this one project only, out of both the Completed-stage gate
    # (project_service._assert_stage_exit_criteria) and the weighted
    # %complete calculation (_recompute_progress), which renormalizes
    # against the remaining included weight so the scale still reads
    # 0-100. Toggled from the project's own checklist, not admin.
    is_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    excluded_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    completion_percentage: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Set when this step was checked complete via the Execution &
    # Tracking stage's "Were any additional services rendered?" flow
    # (project_service.mark_additional_execution_step) rather than being
    # part of the project's original quoted scope -- distinguishes real
    # extra work delivered mid-project from the standard process
    # checklist. contract_covered records the answer to the follow-up
    # "is this covered under the contract?" question asked at the same
    # time -- None until that flow actually runs for this step.
    is_additional_scope: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contract_covered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
