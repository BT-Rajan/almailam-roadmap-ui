from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column


from app.core.database import Base
from app.models.mixins import EmailOtpMixin, SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

PROJECT_STATUSES = ("Active", "On Hold", "Cancelled", "Completed")
# "Correction" used to be its own stage (Review <-> Correction, looping
# back and forth for what's really one review cycle). Merged into
# Review -- see migration 0019 -- since a stage transition wasn't
# adding anything a reason-carrying note in the project's own history
# doesn't already cover, and the back-and-forth stage hopping was
# exactly the kind of thing worth collapsing rather than routing
# elsewhere.
#
# "Enquiry" was itself renamed to "Requirement" (migration 0038) -- it
# now has its own dedicated tab (ProjectRequirementTab.vue) for managing
# the scope-of-work text with revision history. It originally gated the
# move to "Quotation" behind a staff-only internal approval step *plus*
# a client OTP confirmation (see scope_status/PROJECT_SCOPE_STATUSES and
# project_service.approve_scope_of_work in prior revisions) -- migration
# 0079 dropped the internal approval step entirely. The project
# associate's own direct confirmation (scope_client_confirmed_at below
# -- no client-facing step at all, see project_service.
# confirm_requirement_scope) is now the sole sign-off required to leave
# Requirement.
#
# "Execution & Tracking" and "Completed" were removed entirely
# (migration 0051) -- the 23-step execution checklist, the 5-stage
# approval-process gates, and the whole notion of a project reaching a
# terminal "Completed" workflow stage/status went with them. Government
# Submission is now the last stage.
#
# "Completed" comes back as a PROJECT_STATUS (not a WORKFLOW_STAGE --
# migration 0073) once Design/Government Submission/Supervision stop
# being a strict linear chain and become independent parallel tracks
# (see compute_stage_flags, ProjectSelectedActivity.status,
# ProjectSelectedPermit, ProjectSelectedSupervisionActivity.status
# below, and project_service.try_complete_project). This time it's
# real gating: every planned Design/Permit/Supervision item Complete
# or Cancelled, the project's current total value fully paid, and the
# client having acknowledged a handover email -- not the removed
# execution checklist coming back.
#
# "Supervision" (migration 0056) is an independent add-on stage -- a
# project can include Design, Government Submission (Permits),
# Supervision, any combination, or none, depending on which
# activities/permits were picked (see project_service.
# compute_stage_flags).
#
# "Payment Plan" (migration 0061) sits between Quotation and Contract --
# the financial agreement(s) (contract value, payment schedule) now have
# to be generated AND explicitly approved before a contract is even
# drafted, not created as an afterthought partway through Contract once
# a signed contract already exists. See FinancialAgreement.status
# (backend/app/models/payment.py) and payment_service.approve_agreement.
#
# "Handover" (migration 0089) replaces the old shape where Design ->
# Government Submission -> Supervision was a fixed sequential chain and
# "project completion" lived entirely outside the stage machine, as a
# project.status flip gated by a separate _all_tracks_closed check.
# Design, Government Submission, and Supervision now run in PARALLEL,
# independent tracks off Contract -- a project takes whichever of the
# three it actually includes (see compute_stage_flags), in no particular
# order, and all of them converge on Handover once done (see
# project_service._assert_stage_exit_criteria's Handover branch and
# core/status_transitions.PROJECT_STAGE_ALLOWED_TRANSITIONS for the
# actual graph). Handover itself is where the project's payment gets a
# manual confirmation (handover_payment_confirmed_at below) and the
# client's signed acknowledgment is collected (confirm_project_handover)
# before project.status finally becomes "Completed".
WORKFLOW_STAGES = (
    "Requirement",
    "Quotation",
    "Payment Plan",
    "Contract",
    "Design",
    "Government Submission",
    "Supervision",
    "Handover",
)
# Status of one selected Design/Supervision activity instance on a
# project (migration 0073) -- "Not Started"/"In Progress" are
# informational only (nothing currently distinguishes them beyond
# staff's own judgment); "Complete" is what
# project_service.try_complete_project waits on, and "Cancelled" lets
# a descoped activity stop blocking that check without pretending it
# was actually done. See ProjectSelectedActivity.status and
# ProjectSelectedSupervisionActivity.status below.
SELECTED_ACTIVITY_STATUSES = ("Not Started", "In Progress", "Complete", "Cancelled")
# Supervision activities are gated the same way Permits are (migration
# 0074) -- "Planned" until their admin-defined SupervisionPrerequisite
# Design activities are all Complete, then "Eligible"; "In Progress"/
# "Complete"/"Cancelled" set directly by the user from there (no
# sub-tasks, same as Permits). See ProjectSelectedSupervisionActivity
# below and project_service._recompute_supervision_eligibility.
SELECTED_SUPERVISION_STATUSES = ("Planned", "Eligible", "In Progress", "Complete", "Cancelled")


class Project(Base, TimestampMixin, SoftDeleteMixin, EmailOtpMixin):
    __tablename__ = "projects"
    # See migration 0091 -- deleted_at IS NULL is the baseline filter on
    # every project query (project_service.list_projects), on top of
    # whichever of these two is the actual filter in play (the
    # dashboard/stage-scoped views, or ProjectsPage's own status filter).
    __table_args__ = (
        Index("idx_projects_deleted_stage", "deleted_at", "current_stage"),
        Index("idx_projects_deleted_status", "deleted_at", "status"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Free-text project/plot address (migration 0063) -- the site this
    # project is for, separate from any of the client's own
    # ClientAddress rows. Only consumed to fill a Quotation/Contract
    # document template's address placeholder (see
    # document_template_service.MERGE_FIELD_CATALOG).
    site_address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Set once the project associate confirms the scope of work (the
    # `description` field above) is finalized (see
    # project_service.confirm_requirement_scope) -- required to leave
    # the Requirement stage (see _assert_stage_exit_criteria). No
    # client-facing sign-off is involved. Cleared whenever the scope
    # text changes again (save_scope_of_work) -- a confirmation is a
    # sign-off on specific text.
    scope_client_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Comma-joined summary of the distinct service/Supervision/Permit
    # names picked in the New Project wizard's service picker (see
    # NewProjectWizardPage.handleServicesConfirmed) -- a display label,
    # not a normalized reference to the service catalog. 100 chars was
    # too narrow for this: each catalog service name alone can run to
    # 150 (see SelectedActivityIn.serviceName), so joining more than a
    # couple of distinct services/categories -- entirely possible with
    # a large catalog -- overflowed it. Widened to 2000, matching
    # projects.description's own cap, rather than picking a new
    # arbitrary ceiling (migration 0090).
    service: Mapped[str] = mapped_column(String(2000), nullable=False)
    engineer_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    current_stage: Mapped[str] = mapped_column(
        Enum(*WORKFLOW_STAGES, name="project_workflow_stage"), nullable=False, default="Requirement"
    )
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
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
    # Nominal combined monthly rate across this project's selected
    # Supervision activities (migration 0059, renamed from
    # type_activity_total) -- informational only, not prorated; the real
    # billed schedule lives in payment_obligations once a Supervision
    # financial agreement exists (see
    # payment_calculations.generate_prorated_monthly_schedule).
    supervision_monthly_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # The overall Supervision engagement window for this project, entered
    # separately from each selected Supervision activity's own
    # start_date/end_date (ProjectSelectedSupervisionActivity below) --
    # both are captured independently at project setup, per the user's
    # confirmation that the two shouldn't be conflated.
    supervision_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    supervision_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # migration 0087 -- the document_templates row this project's
    # Payment Plan document was rendered against, pinned the first time
    # it's generated (see
    # document_template_service.render_payment_plan_document). Unlike
    # Quotation/Contract there's no single "finalized" record to key
    # off, so first generation is what defines the permanent version
    # here.
    payment_plan_template_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("document_templates.id", ondelete="RESTRICT"), nullable=True
    )
    # Handover / project-completion (migration 0073, restructured around
    # the real "Handover" WORKFLOW_STAGE in migration 0089) -- set by
    # the Handover-entry hook in project_service._apply_stage_change,
    # which only ever fires once every included Design/Permit/
    # Supervision track is Complete/Cancelled (see
    # _assert_stage_exit_criteria's Handover branch). handover_sent_at/
    # handover_acknowledged_at track the ready-for-handover notice and
    # the client's confirmation of it via a signed-document upload (see
    # notify_handover_ready/confirm_project_handover) -- EmailOtpMixin's
    # columns below are inert leftovers now (see its docstring). status
    # only becomes "Completed" once handover_acknowledged_at is set, and
    # confirm_project_handover requires handover_payment_confirmed_at
    # first -- an email that fails to send never blocks this internally,
    # it only notifies Administrators (see notify_role) so someone can
    # resend.
    handover_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    handover_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Manual payment attestation from the Handover stage's Payment
    # Confirmation tab (migration 0089) -- independent of the automatic
    # payment_service.get_project_payment_status() reading shown
    # alongside it as reference; required before confirm_project_
    # handover accepts the signed acknowledgment (see
    # project_service.confirm_handover_payment/unconfirm_handover_payment).
    handover_payment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    handover_payment_confirmed_by: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Free-text closing remarks for the Handover stage's Notes and
    # Report tab (migration 0089) -- a single editable field, not a
    # running log (see timeline_service for that). See
    # project_service.update_handover_notes.
    handover_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Notification guards for the two new periodic checks in
    # project_service (mirrors stale_notified_at's pattern above): a
    # project whose planned activities are all done but isn't yet
    # fully paid, and a project past its target_date. Neither is
    # cleared by set_stage() (unlike stale_notified_at) since track
    # completion/payment isn't tied to workflow_stage changes --
    # cleared explicitly wherever the underlying condition resolves
    # (payment completes / target_date is pushed out).
    unpaid_completion_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    overdue_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProjectScopeRevision(Base):
    """Mirrors QuotationRevision/ContractRevision -- one row per saved
    change to the Requirement stage's scope-of-work text
    (project.description), written automatically by
    project_service.save_scope_of_work. This history is specifically the
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
    # Task-driven completion (migration 0073) -- see Task.
    # selected_activity_id and project_service.
    # _maybe_auto_close_design_activity: closing every Task linked to
    # this row auto-sets status to "Complete", but the user always has
    # a direct manual override (close_design_activity/
    # reopen_design_activity) regardless of task state.
    status: Mapped[str] = mapped_column(
        Enum(*SELECTED_ACTIVITY_STATUSES, name="design_activity_status"), nullable=False, default="Not Started"
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class ProjectSelectedSupervisionActivity(Base):
    """The Supervision activities picked in ServicePickerDialog at project
    creation (migration 0059, replacing ProjectSelectedTypeActivity and
    the old, separate "Additional Activity Catalog") -- one row per
    checked activity, same snapshot approach as ProjectSelectedActivity
    above (activity_id is the catalog's display id, kept as-is rather
    than FK'd, so a later rename or price change doesn't retroactively
    alter what this project was actually quoted). Always Supervision --
    there's no category_name/is_covered_by_service anymore, since Design
    and Supervision are different deliverables on different billing
    cycles with no realistic overlap to reconcile.

    start_date/end_date are this activity's own window, independent of
    the project's overall supervision_start_date/supervision_end_date
    (Project above) -- both are captured separately, per the user's
    confirmation. Once a Supervision financial agreement is created,
    these dates drive the real, day-prorated monthly billing schedule
    (see payment_calculations.generate_prorated_monthly_schedule).
    end_date is required (migration 0081 backfilled the rows that
    predate that) -- it used to be optional, which let a project reach
    Payment Plan with no way to actually create the Supervision
    agreement (_compute_contract_terms hard-requires it); see
    SelectedSupervisionActivityIn's own comment in schemas/project.py."""

    __tablename__ = "project_selected_supervision_activities"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_id: Mapped[str] = mapped_column(String(20), nullable=False)
    activity_name: Mapped[str] = mapped_column(String(150), nullable=False)
    monthly_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Gated like a Permit (migration 0074) -- "Planned" until every
    # SupervisionPrerequisite Design activity is Complete, then
    # "Eligible"; from there the user sets "In Progress"/"Complete"/
    # "Cancelled" directly whenever they judge it done (based on
    # site-engineer input) -- Supervision has no sub-tasks, so this is
    # never auto-derived the way Design's status is. See
    # project_service.set_supervision_status/
    # _recompute_supervision_eligibility.
    status: Mapped[str] = mapped_column(
        Enum(*SELECTED_SUPERVISION_STATUSES, name="supervision_activity_status"), nullable=False, default="Planned"
    )
    eligibility_met_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    eligibility_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[int | None] = mapped_column(BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
