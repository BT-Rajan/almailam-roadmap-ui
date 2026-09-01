from datetime import date, datetime, timedelta, timezone

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    PROJECT_STAGE_ALLOWED_TRANSITIONS,
    PROJECT_STAGE_STATUSES_REQUIRING_REASON,
    PROJECT_STATUS_ALLOWED_TRANSITIONS,
    PROJECT_STATUS_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.client import ClientIdentification
from app.models.contract import Contract, ContractRevision
from app.models.document import ProjectDocument
from app.models.government import GovernmentSubmission
from app.models.project import (
    Project,
    ProjectScopeRevision,
    ProjectSelectedActivity,
    ProjectSelectedSupervisionActivity,
)
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.user import User
from app.services import audit_service, client_service, company_service, notification_service, payment_service, timeline_service, user_service
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


def get_selected_supervision_activities(db: Session, project_id: int) -> list[ProjectSelectedSupervisionActivity]:
    return (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(ProjectSelectedSupervisionActivity.project_id == project_id)
        .order_by(ProjectSelectedSupervisionActivity.id.asc())
        .all()
    )


def get_selected_supervision_activities_batch(
    db: Session, project_ids: set[int]
) -> dict[int, list[ProjectSelectedSupervisionActivity]]:
    """Batch version of get_selected_supervision_activities, same
    reasoning as get_selected_activities_batch above."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedSupervisionActivity]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(ProjectSelectedSupervisionActivity.project_id.in_(project_ids))
        .order_by(ProjectSelectedSupervisionActivity.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def _persist_supervision_selection(
    db: Session,
    project_id: int,
    selection: list,
    supervision_start_date,
    supervision_end_date,
) -> float | None:
    """Validates each selected Supervision activity's own dates against
    the project's overall supervision window (when the window's bounds
    are set) and inserts one ProjectSelectedSupervisionActivity row per
    activity. Returns the nominal combined monthly total (informational
    only -- see Project.supervision_monthly_total), or None if nothing
    was selected."""
    if not selection:
        return None

    for activity in selection:
        if supervision_start_date is not None and activity.startDate < supervision_start_date:
            raise ValidationAppError(
                f"'{activity.activityName}' starts before the overall Supervision start date."
            )
        if supervision_end_date is not None:
            activity_end = activity.endDate or activity.startDate
            if activity_end > supervision_end_date:
                raise ValidationAppError(
                    f"'{activity.activityName}' extends past the overall Supervision end date."
                )

    for activity in selection:
        db.add(
            ProjectSelectedSupervisionActivity(
                project_id=project_id,
                activity_id=activity.activityId,
                activity_name=activity.activityName,
                monthly_rate=activity.monthlyRate,
                start_date=activity.startDate,
                end_date=activity.endDate,
            )
        )

    return sum(float(a.monthlyRate) for a in selection)


def compute_stage_flags(selected_activities: list, selected_supervision_activities: list) -> tuple[bool, bool]:
    """(includes_design, includes_supervision) -- whether this project's
    workflow should offer a Design stage/tab and/or a Supervision one
    (see WORKFLOW_STAGES). Deterministic since migration 0059: Design
    services and the single Supervision service are different branches
    of the same catalog now, so which rows exist says everything --
    no more name-matching against category/service names."""
    return (len(selected_activities) > 0, len(selected_supervision_activities) > 0)


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
    selected_supervision_activities = payload.selectedSupervisionActivities or []
    if selected_supervision_activities and payload.supervisionStartDate is None:
        raise ValidationAppError("supervisionStartDate is required when Supervision activities are selected.")

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
        required_permit_documents=payload.requiredPermitDocuments or [],
        supervision_start_date=payload.supervisionStartDate,
        supervision_end_date=payload.supervisionEndDate,
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

    project.supervision_monthly_total = _persist_supervision_selection(
        db, project.id, selected_supervision_activities, payload.supervisionStartDate, payload.supervisionEndDate,
    )

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
    # current_stage (see recompute_progress), not typed in by hand. See
    # ProjectUpdate's own schema comment.
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
    """See docs/PROJECT_WORKFLOW_MAP for the source diagram. Requirement
    -> Quotation -> Contract is a straight line for every project; what
    comes after Contract depends on which of Design/Supervision this
    project actually includes (see compute_stage_flags) -- Contract ->
    [Design] -> [Supervision] -> Government Submission, skipping
    whichever of Design/Supervision don't apply. Design, when it
    applies, must be approved by the client before Government Submission
    begins (you can't submit unapproved drawings to an authority for
    permit approval) -- that's the "at least one design link" check
    below, gated on *leaving* Design rather than on entering Government
    Submission specifically, since Design might be followed by
    Supervision instead. PROJECT_STAGE_ALLOWED_TRANSITIONS keeps
    reopening paths backward (Government Submission -> Design/
    Supervision, for when an authority's feedback requires changes) --
    those require a reason like any other reopening.
    """
    if new_stage in ("Design", "Supervision"):
        includes_design, includes_supervision = compute_stage_flags(
            get_selected_activities(db, project.id), get_selected_supervision_activities(db, project.id),
        )
        if new_stage == "Design" and not includes_design:
            raise ValidationAppError(
                "This project's selected services/activities don't include Design work -- "
                "there's no Design stage for it to move into."
            )
        if new_stage == "Supervision" and not includes_supervision:
            raise ValidationAppError(
                "This project's selected services/activities don't include Supervision work -- "
                "there's no Supervision stage for it to move into."
            )

    problems: list[str] = []

    if new_stage == "Quotation":
        # The vital requirement for leaving Requirement -- the client's
        # identification (Civil ID for an individual, Trade Licence for
        # an organization, etc.) has to be on file before real
        # commercial work starts. Not part of ClientCreate itself
        # (identification is added separately, after the client
        # record exists -- see client_service.create_identification),
        # so a client can genuinely exist with none yet; this is a
        # real, sometimes-blocking gate, not a formality that's always
        # already satisfied by the time a project exists.
        has_identification = (
            db.query(ClientIdentification)
            .filter(ClientIdentification.client_id == project.client_id, ClientIdentification.deleted_at.is_(None))
            .first()
            is not None
        )
        if not has_identification:
            problems.append("the client's identification document (e.g. Civil ID) on file")
        # The other half of the Requirement stage's redesign -- scope of
        # work has to be reviewed and internally approved before the
        # project can move into commercial quoting, not just have some
        # text sitting in Draft.
        if project.scope_status != "Approved":
            problems.append("the scope of work approved")

    elif new_stage == "Contract":
        approved_quotation = (
            db.query(Quotation)
            .filter(Quotation.project_id == project.id, Quotation.status == "Approved", Quotation.deleted_at.is_(None))
            .first()
        )
        if approved_quotation is None:
            problems.append("an Approved quotation")

    elif previous_stage == "Contract":
        # Gates leaving Contract into whichever of Design/Supervision/
        # Government Submission is actually next for this project -- not
        # just "entering Design" specifically, since a supervision-only
        # (or neither) project skips straight past it. A contract has to
        # actually be signed, not merely exist as a Draft -- this is what
        # "Documents Signed" means in practice (the separate
        # documents_signed approval-process gate used to be checked here
        # instead, but that's a second, easy-to-forget manual upload
        # nothing else in the flow prompts anyone to do; the contract's
        # own status is the real, already-visible signal for this).
        signed_contract = (
            db.query(Contract)
            .filter(
                Contract.project_id == project.id,
                Contract.status.in_(("Signed", "Active")),
                Contract.deleted_at.is_(None),
            )
            .first()
        )
        if signed_contract is None:
            problems.append("a signed contract")
        # A financial agreement -- payment dates and amounts -- has to be
        # prepared right after the contract, not left until later. Only
        # the agreement's existence is required here, not that it's
        # fully paid -- payment is expected to happen across the
        # project's lifetime, tracked by the reminder job below. Checked
        # per stream (migration 0059) -- a project that includes both
        # Design and Supervision needs both agreements, not just one.
        includes_design, includes_supervision = compute_stage_flags(
            get_selected_activities(db, project.id), get_selected_supervision_activities(db, project.id),
        )
        if includes_design and payment_service.get_agreement_by_project(db, project.project_no, "Design") is None:
            problems.append("a Design financial agreement (payment dates and amount)")
        if includes_supervision and payment_service.get_agreement_by_project(db, project.project_no, "Supervision") is None:
            problems.append("a Supervision financial agreement (payment dates and amount)")

    elif previous_stage == "Design":
        # Gates leaving Design into whichever of Supervision/Government
        # Submission is next -- Design itself has to have something in
        # it -- at least one drawing link saved (see
        # DesignDocumentDialog.vue, which requires a link on every
        # 'Drawing'-type document it creates) -- before there's anything
        # to have approved in the first place, regardless of what comes
        # after it.
        has_design_link = (
            db.query(ProjectDocument)
            .filter(
                ProjectDocument.project_id == project.id,
                ProjectDocument.type == "Drawing",
                ProjectDocument.external_link.isnot(None),
                ProjectDocument.deleted_at.is_(None),
            )
            .first()
            is not None
        )
        if not has_design_link:
            problems.append("at least one design document link saved")
        # The separate architectural_approval approval-process gate used
        # to also be required here -- dropped as a blocking exit
        # criterion so that saving a design link is genuinely enough on
        # its own to move past Design, matching how this stage is
        # actually meant to work.

    # previous_stage == "Supervision" has no exit criteria yet -- it's a
    # placeholder stage/tab for now (see WORKFLOW_STAGES).

    if problems:
        raise ValidationAppError(
            f"Cannot move this project to '{new_stage}' yet -- missing: {'; '.join(problems)}."
        )


# --- workflow stage / progress -- merged so "how far along is this
# project" is always one consistent story instead of two independently
# maintained numbers. Government Submission is the last stage and has no
# further stage to advance into -- reaching it is the workflow's own
# terminal state; progress simply stops climbing there rather than
# jumping to 100 (there's no separate "done" concept left to represent).
# A project that skips Design and/or Supervision (see compute_stage_flags)
# still just jumps straight to whichever band it actually lands on --
# the bands themselves don't shift around per project, so progress is
# always "how far through the full 6-band scale", not "how far through
# this project's own shorter path".
_STAGE_PROGRESS_BAND: dict[str, int] = {
    "Requirement": 0,
    "Quotation": 1,
    "Contract": 2,
    "Design": 3,
    "Supervision": 4,
    "Government Submission": 5,
}
_PROGRESS_BAND_COUNT = 6


def recompute_progress(db: Session, project: Project) -> int:
    """Derives project.progress from current_stage -- entering a stage
    jumps progress to that stage's band floor. Does not commit --
    callers already do."""
    band = _STAGE_PROGRESS_BAND[project.current_stage]
    progress = round(band * 100 / _PROGRESS_BAND_COUNT)
    project.progress = max(0, min(100, progress))
    return project.progress


def _auto_advance_target(current_stage: str, includes_design: bool, includes_supervision: bool) -> str | None:
    """The one valid next stage for this project once its exit criteria
    (_assert_stage_exit_criteria) are met, so firing it automatically
    doesn't remove a real choice from anyone -- it just saves the
    separate manual click after the condition that already gates it
    becomes true (approving a quotation, signing a contract, saving a
    design link). Which stage that actually is depends on the project --
    Design and/or Supervision are skipped when this project doesn't
    include that kind of work (see compute_stage_flags). Reopening
    (Government Submission -> Design/Supervision) stays manual -- an
    exceptional, reason-required correction, not something that should
    ever happen as a side effect of an unrelated action."""
    if current_stage == "Requirement":
        return "Quotation"
    if current_stage == "Quotation":
        return "Contract"
    if current_stage == "Contract":
        if includes_design:
            return "Design"
        if includes_supervision:
            return "Supervision"
        return "Government Submission"
    if current_stage == "Design":
        return "Supervision" if includes_supervision else "Government Submission"
    if current_stage == "Supervision":
        return "Government Submission"
    return None


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
    # Reopening Government Submission back to Design or Supervision (an
    # authority's feedback requiring changes) is a correction, not the
    # normal forward flow that also targets those same stages (from
    # Contract/Design) -- can't live in the target-only REQUIRING_REASON
    # table, since that only keys on the target state, not where the
    # transition came from.
    if previous_stage == "Government Submission" and new_stage in ("Design", "Supervision"):
        assert_reason_given(reason, f"A reason is required to send the project back to {new_stage}.")

    _apply_stage_change(db, project, new_stage, reason, user_id)

    db.commit()
    db.refresh(project)
    return project


def try_auto_advance_stage(db: Session, project: Project, user_id: int | None) -> None:
    """Automates the manual "move stage" action for the transition
    _auto_advance_target says is next for this project, once its exit
    criteria are already met -- e.g. approving a quotation is exactly
    what _assert_stage_exit_criteria
    already requires before a project can enter "Contract", so there's
    no reason to also wait on a separate click once that becomes true.

    Called from whichever service action just made the criteria true
    (quotation/contract/payment services), before that action's own
    db.commit() -- sharing one transaction so a mid-way failure can't
    leave stage/progress out of sync with the action that triggered it.
    Does not commit itself.

    Silently does nothing if the target stage's exit criteria aren't met
    yet -- "not yet eligible" is the expected, common case here, not a
    failure the caller's own action should be blocked by.
    """
    includes_design, includes_supervision = compute_stage_flags(
        get_selected_activities(db, project.id), get_selected_supervision_activities(db, project.id),
    )
    target_stage = _auto_advance_target(project.current_stage, includes_design, includes_supervision)
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
    # Reopening a Cancelled project is exceptional and source-dependent
    # (unlike "On Hold" -> "Active", the routine, frequent, reason-free
    # resume), so it's checked here rather than in the target-state-only
    # REQUIRING_REASON table.
    if previous_status == "Cancelled" and new_status == "Active":
        assert_reason_given(reason, "A reason is required to reopen a cancelled project.")

    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Status changed", user_id,
        previous_value=previous_status, new_value=new_status, reason=reason,
    )
    project.status = new_status
    db.commit()
    db.refresh(project)
    return project


def _next_scope_revision_label(current: str) -> str:
    # Same 'R0', 'R1', 'R2', ... scheme as quotation/contract revisions.
    if current.startswith("R") and current[1:].isdigit():
        return f"R{int(current[1:]) + 1}"
    return "R1"


def _latest_scope_revision(db: Session, project_id: int) -> ProjectScopeRevision | None:
    return (
        db.query(ProjectScopeRevision)
        .filter(ProjectScopeRevision.project_id == project_id)
        .order_by(ProjectScopeRevision.id.desc())
        .first()
    )


def get_scope_revisions_with_names(db: Session, project_id: int) -> list[tuple[ProjectScopeRevision, str]]:
    revisions = (
        db.query(ProjectScopeRevision)
        .filter(ProjectScopeRevision.project_id == project_id)
        .order_by(ProjectScopeRevision.id.desc())
        .all()
    )
    return [(r, engineer_name(db, r.changed_by)) for r in revisions]


def save_scope_of_work(
    db: Session,
    project_no: str,
    scope_text: str,
    summary: str | None,
    user_id: int,
    file: UploadFile | None = None,
) -> Project:
    """The Requirement stage's own scope-of-work editor. Every save here
    writes a project_scope_revisions row (R0, R1, ...) and, if the
    scope had already been approved, reopens it back to "Draft" -- an
    approval is a sign-off on specific text, not a status that should
    silently keep covering whatever the text becomes after further
    edits."""
    project = get_project(db, project_no)
    scope_text = scope_text.strip()
    if not scope_text:
        raise ValidationAppError("Scope of work cannot be empty.")

    previous_description = project.description
    project.description = scope_text

    storage_key = original_filename = None
    file_size_bytes = None
    if file is not None:
        storage_key, original_filename, file_size_bytes = save_upload(file, "scope-of-work")

    latest = _latest_scope_revision(db, project.id)
    new_label = _next_scope_revision_label(latest.revision) if latest else "R0"
    db.add(
        ProjectScopeRevision(
            project_id=project.id,
            revision=new_label,
            scope_text=scope_text,
            storage_key=storage_key,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            revised_at=date.today(),
            changed_by=user_id,
            summary=(summary or "Scope of work updated").strip(),
        )
    )

    if project.scope_status == "Approved":
        project.scope_status = "Draft"
        project.scope_approved_at = None
        project.scope_approved_by = None

    audit_service.log_field_changes(
        db, ENTITY_TYPE, project.id, {"description": (previous_description, scope_text)}, user_id
    )
    db.commit()
    db.refresh(project)
    return project


def approve_scope_of_work(db: Session, project_no: str, user_id: int) -> Project:
    """Internal approval of the Requirement stage's scope of work --
    "it is internal approval", not a client-facing sign-off. Once
    approved, try_auto_advance_stage picks it up (alongside the client-
    identification check already in _assert_stage_exit_criteria) and
    moves the project straight to "Quotation" without a separate manual
    click."""
    project = get_project(db, project_no)
    if not (project.description or "").strip():
        raise ValidationAppError("Add the scope of work before approving it.")
    if project.scope_status == "Approved":
        return project

    project.scope_status = "Approved"
    project.scope_approved_at = datetime.now(timezone.utc)
    project.scope_approved_by = user_id
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Scope of work approved", user_id)
    timeline_service.create_system_event(
        db, project.id, "note", title="Scope of work approved", description=project.description, actor_id=user_id
    )
    # The session is autoflush=False -- flush first so the exit-criteria
    # check's own fresh queries (e.g. client identification) see
    # everything written so far in this transaction. project.scope_
    # status itself is read as a live in-memory attribute, not a fresh
    # query, so it's already safe either way -- this is for consistency
    # with every other try_auto_advance_stage call site.
    db.flush()
    try_auto_advance_stage(db, project, user_id)

    db.commit()
    db.refresh(project)
    return project


def get_scope_revision_download_target(db: Session, project_id: int, revision_id: int):
    revision = (
        db.query(ProjectScopeRevision)
        .filter(ProjectScopeRevision.id == revision_id, ProjectScopeRevision.project_id == project_id)
        .first()
    )
    if revision is None or not revision.storage_key:
        raise NotFoundError("Scope of work document")
    return resolve_path(revision.storage_key), revision.original_filename


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
    longer an active concern -- a Cancelled project shouldn't keep
    silently accumulating new work against it. Deliberately does NOT
    gate on current_stage (e.g. requiring stage=="Quotation" before a
    quotation can be created) -- staff legitimately draft a quotation
    before formally advancing the stage, and that's a much stricter,
    more debatable rule than "don't add new work to a project that's
    over."""
    if project.status == "Cancelled":
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
