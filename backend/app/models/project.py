from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column


from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_STATUSES = ("Active", "On Hold", "Completed", "Cancelled")
# "Correction" used to be its own stage (Review <-> Correction, looping
# back and forth for what's really one review cycle). Merged into
# Review -- see migration 0019 -- since a stage transition wasn't
# adding anything a reason-carrying note in the project's own history
# doesn't already cover, and the back-and-forth stage hopping was
# exactly the kind of thing worth collapsing rather than routing
# elsewhere.
#
# "Review" was itself renamed to "Execution & Tracking" and "Approval"
# dropped entirely (migration 0022) -- the 23-step execution checklist
# and the 5-stage approval-process stage gates (see execution_step.py /
# approval_process.py) are what actually happen during this stage, so
# "Review" undersold it and a separate "Approval" stage was redundant
# with the stage gates themselves.
WORKFLOW_STAGES = (
    "Enquiry",
    "Quotation",
    "Contract",
    "Design",
    "Government Submission",
    "Execution & Tracking",
    "Completed",
)
PROJECT_PRIORITIES = ("High", "Medium", "Low")


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    engineer_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_stage: Mapped[str] = mapped_column(
        Enum(*WORKFLOW_STAGES, name="project_workflow_stage"), nullable=False, default="Enquiry"
    )
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    priority: Mapped[str] = mapped_column(
        Enum(*PROJECT_PRIORITIES, name="project_priority"), nullable=False, default="Medium"
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*PROJECT_STATUSES, name="project_status"), nullable=False, default="Active"
    )
    # Set by project_service.check_and_notify_stale_projects() once the
    # assigned engineer has been notified that this project hasn't moved
    # in a while -- prevents re-notifying every time the background check
    # runs (see main.py's scheduled job). Cleared the moment the stage
    # actually changes (set_stage()), so a fresh staleness period starts
    # from scratch rather than staying permanently silenced.
    stale_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Sum of the fixed costs of every row in ProjectSelectedActivity below,
    # captured once at project creation (the New Project Wizard's service
    # picker). Kept as its own column -- rather than always summing the
    # child rows -- so it stays stable even if the underlying catalog
    # prices change later, and so callers that only need the number (list
    # views, cards) don't have to join/aggregate for it.
    service_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Permit names the client confirmed, at project setup (New Project
    # Wizard's Permits step), they already hold -- each becomes a
    # mandatory upload requirement on the Documents tab (see
    # ProjectDocumentsTab.vue's permitChecklist, which loosely matches a
    # Government-category link document's name against these). Permits
    # the client does NOT yet have aren't stored here at all -- those
    # become Tasks instead (create_project's caller), since they're work
    # to do, not a document to chase.
    required_permit_documents: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Set once by set_status() the moment status becomes "Completed",
    # cleared if the project is later reopened -- the actual end-of-project
    # timestamp, distinct from target_date (the planned one) and from
    # updated_at (which changes on every unrelated edit). Used to compute
    # the Completion summary's actual-vs-planned duration.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Free-text handover/lessons-learned notes for the Completion summary
    # -- distinct from `description` above (the project's own scope-of-
    # work description, set at creation and shown on Overview).
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # A PM's own annotation on the auto-derived delivery-deviation read
    # (contract revisions beyond R0, plus budget/duration variance) --
    # distinct from completion_notes, which is general handover/lessons-
    # learned text. Never the source of truth for whether something
    # deviated -- that's always computed live in
    # project_service.get_completion_summary -- this is just the PM's
    # explanation layered on top of it.
    deviation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProjectSelectedActivity(Base):
    """The granular service/activity breakdown picked in ServicePickerDialog
    at project creation -- one row per activity. A snapshot of what was
    picked and at what price, not a live reference to the service catalog
    (service_id/activity_id are the catalog's display ids, e.g. 'SVC-001'/
    'ACT-004', kept as-is rather than FK'd, so a later rename or price
    change in the catalog doesn't retroactively alter what this project was
    actually quoted). This is what NewQuotationDialog/NewContractDialog
    read to prefill line items -- before this table existed, the frontend
    computed and sent this breakdown on create but the backend had nowhere
    to put it, so it was silently dropped and never came back on refetch."""

    __tablename__ = "project_selected_activities"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[str] = mapped_column(String(20), nullable=False)
    service_name: Mapped[str] = mapped_column(String(150), nullable=False)
    activity_id: Mapped[str] = mapped_column(String(20), nullable=False)
    activity_name: Mapped[str] = mapped_column(String(150), nullable=False)
    fixed_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
