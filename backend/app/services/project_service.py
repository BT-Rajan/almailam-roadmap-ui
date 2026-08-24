from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    PROJECT_STAGE_ALLOWED_TRANSITIONS,
    PROJECT_STAGE_STATUSES_REQUIRING_REASON,
    PROJECT_STATUS_ALLOWED_TRANSITIONS,
    PROJECT_STATUS_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.contract import Contract, ContractRevision
from app.models.document import ProjectDocument
from app.models.government import GovernmentSubmission
from app.models.project import Project, ProjectSelectedActivity
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.user import User
from app.services import approval_process_service, audit_service, client_service, company_service, execution_step_service, notification_service, payment_service, timeline_service, user_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "PROJECT"

# Columns the project list can be sorted on via ?sort=field / ?sort=-field.
# Deliberately limited to real columns on the table -- "clientName" and
# "engineer" are resolved from other tables per-row and are not sortable
# without a join, so they're intentionally left out here.
PROJECT_SORTABLE_FIELDS = {
    "projectNo": Project.project_no,
    "projectName": Project.project_name,
    "status": Project.status,
    "priority": Project.priority,
    "currentStage": Project.current_stage,
    "progress": Project.progress,
    "targetDate": Project.target_date,
}


def engineer_name(db: Session, engineer_id: int) -> str:
    user = db.query(User).filter(User.id == engineer_id).first()
    return user.full_name if user else "Unknown"


def engineer_names(db: Session, engineer_ids: set[int]) -> dict[int, str]:
    """Batch lookup used by the list endpoint so it doesn't run one query
    per row (see engineer_name for the single-id version used elsewhere)."""
    if not engineer_ids:
        return {}
    return dict(db.query(User.id, User.full_name).filter(User.id.in_(engineer_ids)).all())


def list_projects(
    db: Session,
    client_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    stage: str | None = None,
    engineer_id: str | None = None,
    search: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    query = db.query(Project).filter(Project.deleted_at.is_(None))
    if client_id:
        query = query.filter(Project.client_id == client_service.parse_client_id(client_id))
    if status:
        query = query.filter(Project.status == status)
    if priority:
        query = query.filter(Project.priority == priority)
    if stage:
        query = query.filter(Project.current_stage == stage)
    if engineer_id:
        query = query.filter(Project.engineer_id == user_service.parse_user_id(engineer_id))
    if search:
        term = f"%{search.strip()}%"
        conditions = [
            Project.project_no.ilike(term),
            Project.project_name.ilike(term),
            Project.service.ilike(term),
        ]
        matching_engineer_ids = [
            row[0] for row in db.query(User.id).filter(User.full_name.ilike(term)).all()
        ]
        if matching_engineer_ids:
            conditions.append(Project.engineer_id.in_(matching_engineer_ids))
        query = query.filter(or_(*conditions))
    return sort_and_paginate(query, Project, PROJECT_SORTABLE_FIELDS, sort, page, page_size)


def get_project(db: Session, project_no: str) -> Project:
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.is_(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Project")
    return project


def get_projects_by_client(db: Session, client_id: str) -> list[Project]:
    return list_projects(db, client_id=client_id)


def get_selected_activities(db: Session, project_id: int) -> list[ProjectSelectedActivity]:
    return (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.project_id == project_id)
        .order_by(ProjectSelectedActivity.id.asc())
        .all()
    )


def get_selected_activities_batch(db: Session, project_ids: set[int]) -> dict[int, list[ProjectSelectedActivity]]:
    """Batch version of get_selected_activities for list endpoints, so
    rendering a page of projects doesn't run one query per row (same
    pattern as engineer_names above)."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedActivity]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.project_id.in_(project_ids))
        .order_by(ProjectSelectedActivity.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def create_project(db: Session, payload, user_id: int | None) -> Project:
    client = client_service.get_client(db, client_service.parse_client_id(payload.clientId))
    if client.onboarding_state != "Ready":
        raise ValidationAppError(
            "A project can only be created for a client whose onboarding is complete "
            f"(current status: '{client.onboarding_state}'). Finish onboarding this client first."
        )
    if client.status != "Active":
        raise ValidationAppError(
            f"This client is marked '{client.status}' and cannot have new projects created for them. "
            "Reactivate the client first."
        )
    engineer_id = user_service.parse_user_id(payload.engineerId)
    engineer = (
        db.query(User)
        .filter(User.id == engineer_id, User.deleted_at.is_(None), User.is_active.is_(True))
        .first()
    )
    if engineer is None:
        raise ValidationAppError("engineerId does not refer to a known, active user.")

    project_no = next_number(db, "PROJECT")
    # If the caller didn't send an explicit serviceTotal (older clients),
    # fall back to summing the picked activities' fixedCost ourselves --
    # keeps the column meaningful even without relying on the frontend's
    # arithmetic being present in the payload.
    selected_activities = payload.selectedActivities or []
    service_total = (
        float(payload.serviceTotal)
        if payload.serviceTotal is not None
        else (sum(float(a.fixedCost) for a in selected_activities) if selected_activities else None)
    )
    project = Project(
        project_no=project_no,
        project_name=payload.projectName,
        description=payload.description,
        client_id=client.id,
        service=payload.service,
        engineer_id=engineer.id,
        priority=payload.priority,
        start_date=payload.startDate,
        target_date=payload.targetDate,
        service_total=service_total,
    )
    db.add(project)
    db.flush()

    for activity in selected_activities:
        db.add(
            ProjectSelectedActivity(
                project_id=project.id,
                service_id=activity.serviceId,
                service_name=activity.serviceName,
                activity_id=activity.activityId,
                activity_name=activity.activityName,
                fixed_cost=activity.fixedCost,
            )
        )

    # Progress is computed from these, not typed in by hand -- see
    # execution_step_service.py. Every project starts at 0% with the
    # full checklist ahead of it, snapshotted from the current admin
    # template so later template edits don't retroactively shift this
    # project's own numbers.
    execution_step_service.snapshot_steps_for_project(db, project.id)

    # Separate, new, standalone trial -- see approval_process.py's own
    # docstring. Deliberately independent of the execution-step
    # snapshot above; nothing about this needs to be scoped to it.
    approval_process_service.snapshot_steps_for_project(db, project.id)

    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project created", user_id, new_value=project.project_name)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_no: str, payload, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    changes: dict[str, tuple] = {}

    if payload.projectName is not None and payload.projectName != project.project_name:
        changes["project_name"] = (project.project_name, payload.projectName)
        project.project_name = payload.projectName
    if payload.description is not None:
        new_description = payload.description.strip() or None
        if new_description != project.description:
            changes["description"] = (project.description, new_description)
        project.description = new_description
    if payload.service is not None and payload.service != project.service:
        changes["service"] = (project.service, payload.service)
        project.service = payload.service
    if payload.priority is not None and payload.priority != project.priority:
        changes["priority"] = (project.priority, payload.priority)
        project.priority = payload.priority
    if payload.targetDate is not None and payload.targetDate != project.target_date:
        if payload.targetDate <= project.start_date:
            raise ValidationAppError("targetDate must be after the project's startDate.")
        changes["target_date"] = (project.target_date, payload.targetDate)
        project.target_date = payload.targetDate
    # progress is deliberately not settable here -- it's computed from
    # the execution-step checklist (execution_step_service.py), not
    # typed in by hand. See ProjectUpdate's own schema comment.
    if payload.engineerId is not None:
        new_engineer_id = user_service.parse_user_id(payload.engineerId)
        if new_engineer_id != project.engineer_id:
            # Same check create_project() uses -- this path was missing
            # it entirely before, meaning a project could be reassigned
            # to a soft-deleted (removed) user with no validation at all.
            engineer = (
                db.query(User)
                .filter(User.id == new_engineer_id, User.deleted_at.is_(None), User.is_active.is_(True))
                .first()
            )
            if engineer is None:
                raise ValidationAppError("engineerId does not refer to a known, active user.")
            changes["engineer_id"] = (project.engineer_id, new_engineer_id)
            project.engineer_id = new_engineer_id

    audit_service.log_field_changes(db, ENTITY_TYPE, project.id, changes, user_id)
    db.commit()
    db.refresh(project)

    if payload.currentStage is not None and payload.currentStage != project.current_stage:
        project = set_stage(db, project_no, payload.currentStage, payload.reason, user_id)
    if payload.status is not None and payload.status != project.status:
        project = set_status(db, project_no, payload.status, payload.reason, user_id)

    return project


# Per-transition exit criteria -- see docs/PROJECT_WORKFLOW_MAP for the
# source diagram this implements. Keyed by the target stage, since each
# entry describes what must be true of the stage being LEFT before the
# move is allowed; PROJECT_STAGE_ALLOWED_TRANSITIONS already guarantees
# only one stage can be "previous_stage" for any given new_stage, so the
# target alone is enough to know which check applies.
def _assert_stage_exit_criteria(db: Session, project: Project, previous_stage: str, new_stage: str) -> None:
    """See docs/PROJECT_WORKFLOW_MAP for the source diagram. Design and
    Government Submission run in parallel (PROJECT_STAGE_ALLOWED_
    TRANSITIONS allows entering either first out of Contract, and moving
    freely between the two), so their checks are organized around that
    fork/converge shape rather than one check per named stage:
      - leaving "Contract" for the first time (whichever of the two
        branches is entered first) requires the Contract-completion
        items, once
      - entering "Execution & Tracking" -- where both branches converge
        -- requires every gate from BOTH branches, regardless of which
        branch was current last
    """
    problems: list[str] = []

    if new_stage == "Contract":
        approved_quotation = (
            db.query(Quotation)
            .filter(Quotation.project_id == project.id, Quotation.status == "Approved", Quotation.deleted_at.is_(None))
            .first()
        )
        if approved_quotation is None:
            problems.append("an Approved quotation")

    elif previous_stage == "Contract" and new_stage in ("Design", "Government Submission"):
        contract_exists = (
            db.query(Contract).filter(Contract.project_id == project.id, Contract.deleted_at.is_(None)).first()
        )
        if contract_exists is None:
            problems.append("a contract")
        gate = approval_process_service.get_project_step_by_stage(db, project.id, "documents_signed")
        if gate.storage_key is None:
            problems.append("the 'Documents Signed' stage gate")
        # A financial agreement -- payment dates and amounts -- has to be
        # prepared right after the contract, not left until the project
        # is finishing up (that's what the "Completed" check further
        # down is for; this one is deliberately earlier). Only the
        # agreement's existence is required here, not that it's fully
        # paid -- payment is expected to happen across the project's
        # lifetime, tracked by the reminder job below, and settled by
        # the time "Completed" is reached.
        if payment_service.get_agreement_by_project(db, project.project_no) is None:
            problems.append("a financial agreement (payment dates and amount)")

    # "Execution & Tracking" is reachable from three different previous
    # stages: convergence from either parallel branch ("Design" or
    # "Government Submission" -- both require every gate from both
    # branches, since either could be the one just finished), or
    # reopening from "Completed" (requires nothing here -- those gates
    # were already satisfied once, and reopening already requires its
    # own reason, asserted separately below).
    elif new_stage == "Execution & Tracking" and previous_stage in ("Design", "Government Submission"):
        for stage_key, label in (
            ("architectural_approval", "'Architectural Design Approved by Client'"),
            ("mew_approval", "'MEW Approval'"),
            ("submit_baladia_kfd", "'Submit to Baladia or KFD'"),
            ("permit_approved", "'Permit Approved'"),
        ):
            gate = approval_process_service.get_project_step_by_stage(db, project.id, stage_key)
            if gate.storage_key is None:
                problems.append(f"the {label} stage gate")

    elif new_stage == "Completed":
        # Steps this specific project has excluded (is_excluded) don't
        # count -- they were never applicable to this project, so they
        # can't be the reason it's stuck (see execution_step_service.
        # included_steps / _recompute_progress, which excludes them
        # from %complete the same way).
        steps = execution_step_service.included_steps(execution_step_service.list_project_steps(db, project.id))
        incomplete = [s for s in steps if s.completion_percentage < 100]
        if incomplete:
            problems.append(f"{len(incomplete)} of {len(steps)} execution activities still incomplete")
        agreement = payment_service.get_agreement_by_project(db, project.project_no)
        if agreement is None:
            problems.append("a financial agreement")
        else:
            summary = payment_service.get_financial_summary(db, agreement.id)
            # totalPending is rounded to whole currency units before this
            # check -- a payment that settles the agreement can leave a
            # sub-unit (fils-level) residue behind from installment
            # rounding (see payment_calculations.generate_even_schedule,
            # which folds any remainder into the last installment); that
            # residue should read as paid-in-full, not block the move.
            if round(summary["totalPending"]) > 0:
                problems.append(f"{summary['totalPending']} {agreement.currency} still outstanding")

    if problems:
        raise ValidationAppError(
            f"Cannot move this project to '{new_stage}' yet -- missing: {'; '.join(problems)}."
        )


# --- workflow stage / progress -- merged so "how far along is this
# project" is always one consistent story instead of two independently
# maintained numbers (a 7-value stage the UI reads directly everywhere,
# and a 0-100 progress bar that used to be driven solely by the
# execution checklist -- see recompute_progress below).
#
# "Design" and "Government Submission" share one band since
# PROJECT_STAGE_ALLOWED_TRANSITIONS lets a project move freely between
# them (they run in parallel, not sequentially) -- treating them as
# different sequential slots would make progress visibly jump backward
# when staff switch which branch they're chasing.
_STAGE_PROGRESS_BAND: dict[str, int] = {
    "Enquiry": 0,
    "Quotation": 1,
    "Contract": 2,
    "Design": 3,
    "Government Submission": 3,
    "Execution & Tracking": 4,
}
_PROGRESS_BAND_COUNT = 6  # the 5 bands above, plus "Completed" as the 6th, terminal slot


def recompute_progress(db: Session, project: Project) -> int:
    """Derives project.progress from current_stage -- entering a stage
    jumps progress to that stage's band floor; within "Execution &
    Tracking" the weighted execution-checklist percentage
    (execution_step_service.compute_weighted_completion) fills the rest
    of that final band, since that's the one stage with its own
    continuous, natural progress signal. "Completed" is always exactly
    100. Does not commit -- callers already do.
    """
    if project.current_stage == "Completed":
        progress = 100
    else:
        band = _STAGE_PROGRESS_BAND[project.current_stage]
        floor = band * 100 / _PROGRESS_BAND_COUNT
        if project.current_stage == "Execution & Tracking":
            checklist_pct = execution_step_service.compute_weighted_completion(db, project.id)
            progress = round(floor + (checklist_pct / 100) * (100 / _PROGRESS_BAND_COUNT))
        else:
            progress = round(floor)
    project.progress = max(0, min(100, progress))
    return project.progress


# Every transition below has exactly one valid next stage once its exit
# criteria (_assert_stage_exit_criteria) are met, so firing it
# automatically doesn't remove a real choice from anyone -- it just
# saves the separate manual click after the condition that already
# gates it becomes true (approving a quotation, closing the last
# approval gate, finishing the checklist and settling payment).
# Deliberately excludes "Contract" (a genuine fork between the "Design"
# and "Government Submission" parallel branches -- staff pick which to
# start) and reopening from "Completed" (exceptional, reason-required)
# -- both stay manual, exactly as before.
_AUTO_ADVANCE_TARGET: dict[str, str] = {
    "Enquiry": "Quotation",
    "Quotation": "Contract",
    "Design": "Execution & Tracking",
    "Government Submission": "Execution & Tracking",
    "Execution & Tracking": "Completed",
}


def _apply_stage_change(
    db: Session, project: Project, new_stage: str, reason: str | None, user_id: int | None, event_label: str = "Stage changed"
) -> None:
    previous_stage = project.current_stage
    audit_service.log_event(
        db, ENTITY_TYPE, project.id, event_label, user_id,
        previous_value=previous_stage, new_value=new_stage, reason=reason,
    )
    project.current_stage = new_stage
    # A fresh staleness period starts now that the project has genuinely
    # moved -- otherwise a project that advances after being flagged
    # would stay permanently silenced (stale_notified_at would never get
    # cleared, so it could never be flagged again even after sitting
    # untouched for another 45+ days on its new stage).
    project.stale_notified_at = None
    db.flush()

    # The only automatic, system-generated timeline entry this app
    # produces today -- everything else on the timeline is still a
    # manually-added milestone (see timeline_service.create_event). This
    # is what lets the customer portal's "Recent Updates" feed and the
    # staff Timeline tab show real stage progression at all, rather than
    # being empty until someone remembers to log it by hand.
    timeline_service.create_system_event(
        db, project.id, "stage",
        title=f"Stage advanced to {new_stage}",
        description=reason,
        actor_id=user_id,
    )
    recompute_progress(db, project)


def set_stage(db: Session, project_no: str, new_stage: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    previous_stage = project.current_stage
    assert_transition_allowed(
        PROJECT_STAGE_ALLOWED_TRANSITIONS, previous_stage, new_stage, "project"
    )
    _assert_stage_exit_criteria(db, project, previous_stage, new_stage)
    if new_stage in PROJECT_STAGE_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_stage}'.")
    # Reopening a Completed project is exceptional and source-dependent
    # (unlike "Execution & Tracking" -> "Completed", the normal reason-
    # free outcome of finishing the checklist), so this can't live in
    # the target-state-only REQUIRING_REASON table -- it's checked here
    # instead.
    if previous_stage == "Completed" and new_stage == "Execution & Tracking":
        assert_reason_given(reason, "A reason is required to reopen a completed project.")

    _apply_stage_change(db, project, new_stage, reason, user_id)

    db.commit()
    db.refresh(project)
    return project


def try_auto_advance_stage(db: Session, project: Project, user_id: int | None) -> None:
    """Automates the manual "move stage" action for the transitions in
    _AUTO_ADVANCE_TARGET, once their exit criteria are already met --
    e.g. approving a quotation is exactly what _assert_stage_exit_criteria
    already requires before a project can enter "Contract", so there's
    no reason to also wait on a separate click once that becomes true.

    Called from whichever service action just made the criteria true
    (quotation/approval-process/execution-step/payment services),
    before that action's own db.commit() -- sharing one transaction so a
    mid-way failure can't leave stage/progress out of sync with the
    action that triggered it. Does not commit itself.

    Silently does nothing if the target stage's exit criteria aren't met
    yet -- "not yet eligible" is the expected, common case here, not a
    failure the caller's own action should be blocked by.
    """
    target_stage = _AUTO_ADVANCE_TARGET.get(project.current_stage)
    if target_stage is None:
        return
    try:
        assert_transition_allowed(PROJECT_STAGE_ALLOWED_TRANSITIONS, project.current_stage, target_stage, "project")
        _assert_stage_exit_criteria(db, project, project.current_stage, target_stage)
    except ValidationAppError:
        return
    _apply_stage_change(db, project, target_stage, None, user_id, event_label="Stage auto-advanced")


def set_status(db: Session, project_no: str, new_status: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    previous_status = project.status
    assert_transition_allowed(
        PROJECT_STATUS_ALLOWED_TRANSITIONS, previous_status, new_status, "project"
    )
    if new_status in PROJECT_STATUS_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_status}'.")
    # Reopening a Completed or Cancelled project is exceptional and
    # source-dependent (unlike "On Hold" -> "Active", the routine,
    # frequent, reason-free resume), so it's checked here rather than
    # in the target-state-only REQUIRING_REASON table.
    if previous_status in ("Completed", "Cancelled") and new_status == "Active":
        assert_reason_given(reason, f"A reason is required to reopen a {previous_status.lower()} project.")
    # The two parallel fields (status and current_stage) could otherwise
    # silently disagree -- nothing previously stopped a project still
    # sitting at "Enquiry" stage from being marked "Completed" status.
    if new_status == "Completed" and project.current_stage != "Completed":
        raise ValidationAppError(
            "A project's status can only become 'Completed' once its workflow stage has also "
            f"reached 'Completed' (currently at '{project.current_stage}')."
        )

    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Status changed", user_id,
        previous_value=previous_status, new_value=new_status, reason=reason,
    )
    project.status = new_status
    # The Completion summary's actual-vs-planned duration needs a real
    # "when did this project actually finish" timestamp -- target_date is
    # only ever the plan, and updated_at changes on every unrelated edit.
    # Cleared on reopen so a project completed twice reports its most
    # recent completion, not a stale one from the first time around.
    project.completed_at = datetime.now(timezone.utc) if new_status == "Completed" else None
    # progress is no longer force-set to 100 here. It used to be, so a
    # project marked "Completed" would never show an inconsistent-looking
    # progress bar next to it -- but progress is now computed from the
    # execution-step checklist (execution_step_service.py), not a number
    # staff can freely edit. Overriding it here would mean the number
    # could lie about how much of the actual checklist is done; leaving
    # it alone means the progress bar stays honest even for a project
    # marked Completed with steps still outstanding, which is real,
    # useful information rather than a cosmetic inconsistency to paper
    # over.
    db.commit()
    db.refresh(project)
    return project


def get_completion_summary(db: Session, project_no: str) -> dict:
    """Planned vs. actual budget and duration for the Completion summary
    (Overview tab). Budget is derived entirely from the existing payment
    module -- planned = the project's one FinancialAgreement.contract_
    amount (see migration 0015's one-agreement-per-project constraint),
    actual = total received across it -- rather than a second, hand-typed
    number that could drift from what payments actually show. Duration is
    planned = target_date - start_date, actual = completed_at - start_date
    (None until the project is actually marked Completed)."""
    project = get_project(db, project_no)

    planned_budget: float | None = None
    actual_budget: float | None = None
    agreement = payment_service.get_agreement_by_project(db, project_no)
    if agreement:
        summary = payment_service.get_financial_summary(db, agreement.id)
        planned_budget = float(summary["contractAmount"])
        actual_budget = float(summary["totalReceived"])

    planned_duration_days = (project.target_date - project.start_date).days
    actual_duration_days = (
        (project.completed_at.date() - project.start_date).days if project.completed_at else None
    )

    # Scope deviations -- every ContractRevision beyond a contract's
    # initial R0 across every contract this project has had. A contract
    # only gets a ContractRevision row when its revision actually bumps
    # (see contract_service.add_revision), so an empty list here is a
    # real "nothing changed", not just "we didn't check".
    revisions = (
        db.query(ContractRevision, User)
        .join(Contract, Contract.id == ContractRevision.contract_id)
        .join(User, User.id == ContractRevision.changed_by)
        .filter(Contract.project_id == project.id)
        .order_by(ContractRevision.revised_at.asc(), ContractRevision.id.asc())
        .all()
    )
    scope_deviations = [
        {
            "revision": revision.revision,
            "date": revision.revised_at,
            "changedBy": user.full_name,
            "summary": revision.summary,
        }
        for revision, user in revisions
    ]

    return {
        "plannedBudget": planned_budget,
        "actualBudget": actual_budget,
        "plannedDurationDays": planned_duration_days,
        "actualDurationDays": actual_duration_days,
        "completedAt": project.completed_at,
        "notes": project.completion_notes,
        "scopeDeviations": scope_deviations,
        "deviationNotes": project.deviation_notes,
    }


def update_completion_notes(db: Session, project_no: str, notes: str, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    project.completion_notes = notes.strip() or None
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Completion notes updated", user_id)
    db.commit()
    db.refresh(project)
    return project


def update_deviation_notes(db: Session, project_no: str, notes: str, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    project.deviation_notes = notes.strip() or None
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Deviation notes updated", user_id)
    db.commit()
    db.refresh(project)
    return project


def change_scope(
    db: Session,
    project_no: str,
    new_description: str,
    contract_update_needed: bool,
    payment_update_needed: bool,
    user_id: int | None,
) -> Project:
    """The Execution & Tracking tab's "Change Scope" action. Always
    updates the scope-of-work description (project.description, the
    same field Overview's "What the Customer Asked For" reads); if
    either flag is set, every Administrator is notified to go make the
    corresponding update themselves -- this only records that a scope
    change happened and whether contract/payment need to catch up with
    it, it doesn't touch either of those modules directly."""
    project = get_project(db, project_no)
    new_description = new_description.strip() or None
    previous_description = project.description
    if new_description == previous_description:
        return project

    project.description = new_description
    audit_service.log_field_changes(
        db, ENTITY_TYPE, project.id, {"description": (previous_description, new_description)}, user_id
    )

    flags: list[str] = []
    if contract_update_needed:
        flags.append("contract")
    if payment_update_needed:
        flags.append("payment")
    note = "Scope changed." if not flags else f"Scope changed -- {' and '.join(flags)} update needed."
    timeline_service.create_system_event(db, project.id, "note", title=note, description=new_description, actor_id=user_id)

    if flags:
        admins = db.query(User).filter(User.role == "Administrator", User.deleted_at.is_(None)).all()
        for admin in admins:
            notification_service.create_notification(
                db, admin.id,
                "Project scope changed",
                f"{project.project_name} ({project.project_no})'s scope changed and needs a "
                f"{' and '.join(flags)} update.",
                "Project",
                link_route_name="project-workspace",
                link_params={"projectId": project.project_no},
            )

    db.commit()
    db.refresh(project)
    return project


def _project_exists(db: Session, project_no: str) -> Project:
    """Like get_project() but doesn't exclude soft-deleted projects --
    used only for read-only historical views (audit trail) where a
    deleted project's own history must remain inspectable. Everything
    else (updates, timeline entries, etc.) keeps using get_project() so
    a soft-deleted project stays fully locked for writes."""
    project = db.query(Project).filter(Project.project_no == project_no).first()
    if project is None:
        raise NotFoundError("Project")
    return project


def assert_project_open_for_new_work(project: Project) -> None:
    """Blocks creating new child records (quotations, contracts, tasks,
    documents, government submissions) against a project that's no
    longer an active concern -- a Cancelled or Completed project
    shouldn't keep silently accumulating new work against it. Deliberately
    does NOT gate on current_stage (e.g. requiring stage=="Quotation"
    before a quotation can be created) -- staff legitimately draft a
    quotation before formally advancing the stage, and that's a much
    stricter, more debatable rule than "don't add new work to a project
    that's over."""
    if project.status in ("Cancelled", "Completed"):
        raise ValidationAppError(
            f"This project is marked '{project.status}' and can no longer have new records added to it."
        )


def get_audit_events(db: Session, project_no: str) -> list[dict]:
    project = _project_exists(db, project_no)
    return audit_service.get_history(db, ENTITY_TYPE, project.id)


def delete_project(db: Session, project_no: str, actor_id: int) -> None:
    project = get_project(db, project_no)

    # Same reasoning as client_service.delete_client()'s active-projects
    # check: this is a soft-delete (deleted_at set, not a real row
    # removal), so the real FK constraints on these child tables' project_id
    # never fire to protect against it -- without this check, a project
    # with real quotations/contracts/tasks/documents/submissions still on
    # file could be "deleted" while those records kept silently pointing
    # at it. Queried directly against the models here (not through each
    # sibling service module) to avoid a circular import, since those
    # modules already import project_service themselves for
    # assert_project_open_for_new_work().
    child_counts = {
        "quotation(s)": db.query(Quotation).filter(Quotation.project_id == project.id, Quotation.deleted_at.is_(None)).count(),
        "contract(s)": db.query(Contract).filter(Contract.project_id == project.id, Contract.deleted_at.is_(None)).count(),
        "task(s)": db.query(Task).filter(Task.project_id == project.id, Task.deleted_at.is_(None)).count(),
        "document(s)": db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.deleted_at.is_(None)).count(),
        "government submission(s)": db.query(GovernmentSubmission).filter(GovernmentSubmission.project_id == project.id, GovernmentSubmission.deleted_at.is_(None)).count(),
    }
    existing = [f"{count} {label}" for label, count in child_counts.items() if count > 0]
    if existing:
        raise ValidationAppError(
            f"This project still has {', '.join(existing)} on file and cannot be deleted. "
            "Remove or reassign those first."
        )

    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project deleted", actor_id, previous_value=project.project_name)
    project.deleted_at = datetime.now(timezone.utc)
    db.commit()


def check_and_notify_stale_projects(db: Session) -> int:
    """Finds Active projects whose workflow stage hasn't moved in more
    than the admin-configured threshold (CompanySettings.
    stale_project_alert_days, default 45) and notifies the assigned
    engineer once per staleness episode -- stale_notified_at prevents
    re-notifying every time this runs, and is cleared the moment the
    project's stage actually changes (set_stage()), so a fresh
    staleness period starts from scratch rather than staying
    permanently silenced after one alert.

    Called periodically by the background scheduler (see main.py's
    lifespan), but is itself a plain, directly-callable function --
    deliberately not scheduling logic of its own, so the actual
    staleness decision can be tested without waiting on a real clock.

    Returns how many projects were newly flagged in this run.
    """
    settings = company_service.get_settings(db)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=settings.stale_project_alert_days)

    candidates = (
        db.query(Project)
        .filter(Project.deleted_at.is_(None), Project.status == "Active", Project.stale_notified_at.is_(None))
        .all()
    )

    notified_count = 0
    for project in candidates:
        last_stage_event = timeline_service.get_last_stage_event(db, project.id)
        # A project that has never advanced past its initial stage has
        # no "stage" timeline event yet -- fall back to when the project
        # itself was created, since that's genuinely when its current
        # (first) stage started.
        reference_time = last_stage_event.created_at if last_stage_event else project.created_at

        if reference_time <= cutoff:
            notification_service.create_notification(
                db, project.engineer_id,
                "Project hasn't moved in a while",
                f"{project.project_name} ({project.project_no}) has been at '{project.current_stage}' stage for "
                f"more than {settings.stale_project_alert_days} days without advancing.",
                "Project",
                link_route_name="project-workspace",
                link_params={"projectId": project.project_no},
            )
            project.stale_notified_at = datetime.now(timezone.utc)
            notified_count += 1

    db.commit()
    return notified_count
