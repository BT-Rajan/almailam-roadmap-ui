from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_APPROVAL_STEP_STATUSES = ("Pending", "Completed", "Waived")


class ApprovalProcessTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """The 5-stage Project Approval Process (Documents Signed -> MEW
    Approval -> Architectural Design Approved by Client -> Submit to
    Baladia or KFD -> Permit Approved). This and ExecutionStepTemplate's
    23 steps (see execution_step.py) are the whole of the project
    process -- nothing else in the codebase should define a competing
    notion of "the stages a project design/approval goes through".

    stage_key is this stage's own identity (documents_signed,
    mew_approval, architectural_approval, submit_baladia_kfd,
    permit_approved) -- ExecutionStepTemplate rows reference it via
    their own stage_key to say which of these 5 stages they belong
    under, which is how the unified project Process view (one tab,
    5 stages, each expandable to its related execution steps) groups
    the two lists together. is_optional exists for symmetry with
    ExecutionStepTemplate and to allow a future stage to be marked
    client-waivable, though none of the 5 seeded stages are today.
    """

    __tablename__ = "approval_process_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    stage_key: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProjectApprovalStep(Base, TimestampMixin):
    """One project's own snapshot of the approval process, copied from
    ApprovalProcessTemplate at creation time -- same snapshot-not-live-
    reference reasoning as ProjectExecutionStep. Linear: a step can
    only be completed once every step before it is already Completed
    or Waived, and can only be un-completed if it's the most recently
    resolved one.

    Waived mirrors ProjectExecutionStep.status exactly -- some clients'
    circumstances mean a stage doesn't apply (e.g. a permit already in
    hand from a prior phase), so it can be waived with a reason rather
    than blocking every step after it forever.

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
    stage_key: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_APPROVAL_STEP_STATUSES, name="project_approval_step_status"),
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
