from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text
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
#
# "Enquiry" was itself renamed to "Requirement" (migration 0038) -- it
# now has its own dedicated tab (ProjectRequirementTab.vue) for managing
# the scope-of-work text with revision history and an internal approval
# step, rather than sharing the general Overview tab with "Completed".
# See scope_status/PROJECT_SCOPE_STATUSES below and
# project_service.approve_scope_of_work.
WORKFLOW_STAGES = (
    "Requirement",
    "Quotation",
    "Contract",
    "Design",
    "Government Submission",
    "Execution & Tracking",
    "Completed",
)
PROJECT_PRIORITIES = ("High", "Medium", "Low")
# Internal approval of the project's scope-of-work text (the
# `description` field below) -- set by the Requirement stage's Approve
# action, which is what gates the automatic move to "Quotation" (see
# project_service._assert_stage_exit_criteria / approve_scope_of_work).
# Not client-facing -- "it is internal approval".
PROJECT_SCOPE_STATUSES = ("Draft", "Approved")


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Internal approval of `description` (the scope-of-work text) at the
    # Requirement stage -- see PROJECT_SCOPE_STATUSES above.
    # scope_approved_at/_by are both None until first approved.
    scope_status: Mapped[str] = mapped_column(
        Enum(*PROJECT_SCOPE_STATUSES, name="project_scope_status"), nullable=False, default="Draft"
    )
    scope_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scope_approved_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    engineer_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Which admin-configured execution step set (see
    # ExecutionStepSetTemplate) this project's own checklist was
    # snapshotted from at creation -- see execution_step_service.
    # snapshot_steps_for_project. Nullable/RESTRICT rather than
    # required: an existing project's already-snapshotted
    # ProjectExecutionStep rows are unaffected either way, this is only
    # about which set a *new* snapshot would come from.
    step_set_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("execution_step_set_templates.id", ondelete="RESTRICT"), nullable=True
    )
    current_stage: Mapped[str] = mapped_column(
        Enum(*WORKFLOW_STAGES, name="project_workflow_stage"), nullable=False, default="Requirement"
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
    # The engagement type picked at the New Project wizard's final step
    # (Design/Supervision/etc, from type_activity_categories) -- a plain
    # name snapshot, same "not FK'd" reasoning as `service` above: a later
    # rename of the category shouldn't retroactively alter what this
    # project was actually set up as. Nullable because this step is new;
    # projects created before it exist have no value here.
    type_category_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # Sum of the fixed costs of every row in ProjectSelectedTypeActivity
    # below that was NOT already covered by a selected service activity
    # of the same name -- see project_service.list_uncovered_type_activities
    # for the matching logic. Same "captured once, stays stable" reasoning
    # as service_total.
    type_activity_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
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


class ProjectScopeRevision(Base):
    """Mirrors QuotationRevision/ContractRevision -- one row per saved
    change to the Requirement stage's scope-of-work text
    (project.description), written automatically by
    project_service.save_scope_of_work. Distinct from that same table's
    change_scope() action (the Execution & Tracking tab's "Change Scope"),
    which doesn't write these rows -- this history is specifically the
    pre-Quotation Requirement stage's own revision trail, up to and
    including the revision that got approved."""

    __tablename__ = "project_scope_revisions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[str] = mapped_column(String(10), nullable=False)
    scope_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional supporting document (e.g. a client brief/RFQ) attached to
    # this revision -- same storage_key/original_filename/file_size_bytes
    # shape as ProjectApprovalStep's stage-gate document.
    storage_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    revised_at: Mapped[date] = mapped_column(Date, nullable=False)
    changed_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


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
    # Whether this specific scope item has actually been delivered --
    # toggled from the Execution & Tracking stage's "Scope Execution"
    # checklist (see project_service.set_scope_item_complete), not at
    # creation. This -- not the 23-item generic template -- is what
    # "only scope should be executed" means: a project's real
    # completion gate is whether the services/activities the client was
    # actually quoted for are done, checked here per line rather than
    # inferred from a fixed, service-agnostic process checklist.
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ProjectSelectedTypeActivity(Base):
    """The checkbox breakdown picked at the New Project wizard's final
    step (see ProjectRequirementTypeStep / the type-activity-catalog
    picker), one row per checked activity -- same snapshot approach as
    ProjectSelectedActivity above (type_activity_item_id is the catalog's
    display id, kept as-is rather than FK'd). is_covered_by_service
    records whether this activity's name matched a selected *service*
    activity of the same name at the moment the project was created --
    covered rows don't add to type_activity_total (they're already priced
    under the service), only uncovered ones do. Recorded per-row (rather
    than only ever filtering by name at read time) so the covered/
    uncovered call stays stable even if the project's services are edited
    later -- what actually happened at creation is what was billed."""

    __tablename__ = "project_selected_type_activities"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type_activity_item_id: Mapped[str] = mapped_column(String(20), nullable=False)
    activity_name: Mapped[str] = mapped_column(String(150), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_covered_by_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Same meaning and same reasoning as ProjectSelectedActivity.is_complete
    # above -- a type-activity is just as much a real scope item as a
    # service activity, and is tracked for delivery the same way.
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
