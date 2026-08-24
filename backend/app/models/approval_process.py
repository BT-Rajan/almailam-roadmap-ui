from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK


class ApprovalProcessTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """The 5-stage Project Approval Process (Documents Signed -> MEW
    Approval -> Architectural Design Approved by Client -> Submit to
    Baladia or KFD -> Permit Approved). This and ExecutionStepTemplate's
    23 steps (see execution_step.py) are the whole of the project
    process -- nothing else in the codebase should define a competing
    notion of "the stages a project design/approval goes through".

    stage_key is this stage's own identity (documents_signed,
    mew_approval, architectural_approval, submit_baladia_kfd,
    permit_approved). Despite sharing a column name, ExecutionStepTemplate's
    own stage_key is a disjoint concept (one of the 7 project workflow
    stages, not one of these 5 gates) -- the two templates are two
    genuinely independent tracks, shown as two separate sections on one
    Process tab, not one nested under the other (an earlier attempt at
    exactly that grouping was tried and abandoned, since the 23 steps
    were never actually partitioned one-to-one under these 5 stages).
    A handful of specific steps that duplicate a specific gate closing
    (or a Quotation/Contract being created) auto-complete when that gate
    closes -- see execution_step_service.try_auto_fill and its
    _AUTO_FILL_TRIGGERS table -- but that's a one-directional convenience
    on 7 of the 23 steps, not a structural link between the two
    templates. is_optional exists for symmetry with ExecutionStepTemplate
    and to allow a future stage to be marked client-waivable, though none
    of the 5 seeded stages are today.
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
    reference reasoning as ProjectExecutionStep.

    Since migration 0022, each of these 5 rows is a stage gate: the
    stage counts as complete the moment its review document is
    uploaded (storage_key set, see
    approval_process_service.upload_stage_gate_document). Migration
    0033 added a second, independent path: completed_at/completed_by,
    set once every project_documents row tagged to this stage_key
    (see ProjectDocument.stage_key) is Approved and a user confirms
    (see approval_process_service.complete_stage_from_documents). The
    two paths don't interact -- storage_key never gets cleared by the
    documents path and vice versa. hasDocument (schema layer) still
    means storage_key is set specifically; isComplete means either
    path fired. No order enforced between stages either way.

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
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
