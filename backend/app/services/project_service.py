from datetime import date, datetime, time, timedelta, timezone

from fastapi import UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.core.file_storage import assert_pdf_upload, resolve_path, save_upload
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    PROJECT_STAGE_ALLOWED_TRANSITIONS,
    PROJECT_STAGE_STATUSES_REQUIRING_REASON,
    PROJECT_STATUS_ALLOWED_TRANSITIONS,
    PROJECT_STATUS_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.client import Client, ClientIdentification
from app.models.contract import Contract
from app.models.document import ProjectDocument, ProjectLinkDocument
from app.models.handover_checklist import HandoverChecklistItem
from app.models.payment import FinancialAgreement, Payment
from app.models.permit_selection import ProjectSelectedPermit
from app.models.prerequisite import PermitPrerequisite, SupervisionPrerequisite
from app.models.project import (
    Project,
    ProjectScopeRevision,
    ProjectSelectedActivity,
    ProjectSelectedSupervisionActivity,
)
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.user import User
from app.services import audit_service, client_service, company_service, document_service, email_service, email_template_service, notification_service, payment_service, permit_catalog_service, timeline_service, user_service
from app.services.number_series_service import next_number, next_task_number

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
    deleted: bool = False,
) -> dict:
    query = db.query(Project).filter(Project.deleted_at.isnot(None) if deleted else Project.deleted_at.is_(None))
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


def get_selected_permits(db: Session, project_id: int) -> list[ProjectSelectedPermit]:
    return (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.project_id == project_id)
        .order_by(ProjectSelectedPermit.id.asc())
        .all()
    )


def get_selected_permits_batch(db: Session, project_ids: set[int]) -> dict[int, list[ProjectSelectedPermit]]:
    """Batch version of get_selected_permits, same reasoning as
    get_selected_activities_batch above."""
    if not project_ids:
        return {}
    result: dict[int, list[ProjectSelectedPermit]] = {pid: [] for pid in project_ids}
    rows = (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.project_id.in_(project_ids))
        .order_by(ProjectSelectedPermit.id.asc())
        .all()
    )
    for row in rows:
        result[row.project_id].append(row)
    return result


def get_selected_activity(db: Session, project_id: int, activity_id: int) -> ProjectSelectedActivity:
    """A single Design activity row, scoped to a specific project so a
    caller can't operate on another project's row just by knowing its
    raw id."""
    activity = (
        db.query(ProjectSelectedActivity)
        .filter(ProjectSelectedActivity.id == activity_id, ProjectSelectedActivity.project_id == project_id)
        .first()
    )
    if activity is None:
        raise NotFoundError("Selected activity")
    return activity


def _auto_complete_linked_tasks(db: Session, task_filter, user_id: int | None) -> None:
    """Closes out any task still open under a Design activity/Permit/
    Supervision activity that is itself being force-closed (Complete or
    Cancelled) directly by a user, on top of whatever the task-driven
    auto-close path already covers. Permits and Supervision activities
    are explicitly closeable "anytime as they deem fit" regardless of
    their own linked tasks' status (see set_permit_status/
    set_supervision_status), and even Design allows Cancelled without
    every linked task Completed (a descoped activity doesn't need its
    tasks finished) -- without this, a task nobody individually touched
    stays open forever under a parent the user already declared done,
    and later silently blocks Handover's "every task closed" gate even
    though every service reads as finished. A no-op when nothing linked
    is still open (the common case, e.g. Design's own Complete path,
    which already required every linked task Completed beforehand)."""
    open_tasks = db.query(Task).filter(task_filter, Task.deleted_at.is_(None), Task.status != "Completed").all()
    for task in open_tasks:
        previous = task.status
        task.status = "Completed"
        audit_service.log_event(
            db, "TASK", task.id, "Task auto-completed (parent service closed)", user_id,
            previous_value=previous, new_value="Completed",
        )


def _set_design_activity_status(
    db: Session, activity: ProjectSelectedActivity, new_status: str, user_id: int | None, auto: bool
) -> None:
    previous = activity.status
    activity.status = new_status
    activity.closed_at = datetime.now(timezone.utc)
    activity.closed_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, activity.project_id,
        "Design activity auto-closed (all linked tasks completed)" if auto else "Design activity closed",
        user_id, previous_value=previous, new_value=new_status,
    )
    if not auto:
        _auto_complete_linked_tasks(db, Task.selected_activity_id == activity.id, user_id)
    if new_status == "Complete":
        project = db.query(Project).filter(Project.id == activity.project_id).first()
        if project is not None:
            _recompute_permit_eligibility(db, project)
            _recompute_supervision_eligibility(db, project)


def _recompute_permit_eligibility(db: Session, project: Project) -> None:
    """Whenever a Design activity on this project closes to Complete,
    check every still-"Planned" permit's PermitPrerequisite rows and
    flip it to "Eligible" once all of them are satisfied -- notifying
    every Administrator once (guarded by eligibility_notified_at) so
    the "ready to apply" moment is actually visible to someone, not
    just a silent status flip. A permit with no prerequisites at all is
    eligible immediately (also called once from create_project for
    exactly that case, since it would otherwise never fire for a
    project with no Design activities to close).

    Deliberately one-directional: only ever promotes Planned ->
    Eligible, never demotes an already-Eligible/In Progress/Complete
    permit back down just because some *other* Design activity was
    later reopened -- once staff was told it's fine to start, walking
    that back would be more disruptive than useful. Does not commit --
    callers already do."""
    planned_permits = (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.project_id == project.id, ProjectSelectedPermit.status == "Planned")
        .all()
    )
    if not planned_permits:
        return
    complete_activity_ids = {
        a.activity_id for a in get_selected_activities(db, project.id) if a.status == "Complete"
    }
    for permit in planned_permits:
        if permit.permit_catalog_item_id is None:
            continue
        required_activity_ids = {
            f"ACT-{p.design_activity_id:03d}"
            for p in db.query(PermitPrerequisite)
            .filter(PermitPrerequisite.permit_catalog_item_id == permit.permit_catalog_item_id)
            .all()
        }
        if not required_activity_ids.issubset(complete_activity_ids):
            continue
        permit.status = "Eligible"
        permit.eligibility_met_at = datetime.now(timezone.utc)
        if permit.eligibility_notified_at is None:
            notification_service.notify_role(
                db, "Administrator",
                "Permit ready for application",
                f"{permit.permit_name} is now eligible to apply for on project {project.project_no} "
                "-- its required Design work is complete.",
                "System",
                link_route_name="project-workspace", link_params={"projectId": project.project_no},
            )
            permit.eligibility_notified_at = datetime.now(timezone.utc)


def _recompute_supervision_eligibility(db: Session, project: Project) -> None:
    """Same shape and rationale as _recompute_permit_eligibility above,
    for Supervision activities instead of Permits -- "only when few
    design activities get completed we can start ... same case apply
    for supervision." Also one-directional (only Planned -> Eligible)
    and notifies Administrators once, guarded by
    eligibility_notified_at. Does not commit -- callers already do."""
    planned_activities = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(
            ProjectSelectedSupervisionActivity.project_id == project.id,
            ProjectSelectedSupervisionActivity.status == "Planned",
        )
        .all()
    )
    if not planned_activities:
        return
    complete_design_activity_ids = {
        a.activity_id for a in get_selected_activities(db, project.id) if a.status == "Complete"
    }
    for activity in planned_activities:
        # activity_id is the catalog display id ("ACT-004"), but
        # SupervisionPrerequisite.supervision_activity_id is the
        # catalog's real numeric id -- resolve the one this row was
        # picked from rather than joining through the string snapshot.
        catalog_activity_id = int(activity.activity_id.removeprefix("ACT-")) if activity.activity_id.startswith("ACT-") else None
        if catalog_activity_id is None:
            continue
        required_activity_ids = {
            f"ACT-{p.design_activity_id:03d}"
            for p in db.query(SupervisionPrerequisite)
            .filter(SupervisionPrerequisite.supervision_activity_id == catalog_activity_id)
            .all()
        }
        if not required_activity_ids.issubset(complete_design_activity_ids):
            continue
        activity.status = "Eligible"
        activity.eligibility_met_at = datetime.now(timezone.utc)
        if activity.eligibility_notified_at is None:
            notification_service.notify_role(
                db, "Administrator",
                "Supervision ready to start",
                f"{activity.activity_name} is now eligible to start on project {project.project_no} "
                "-- its required Design work is complete.",
                "System",
                link_route_name="project-workspace", link_params={"projectId": project.project_no},
            )
            activity.eligibility_notified_at = datetime.now(timezone.utc)


def _assert_completion_evidence(db: Session, project: Project, override_no_document: bool) -> None:
    """Gates marking a Design activity/Permit/Supervision activity
    Complete (never Cancelled -- nothing to evidence there) on either a
    Project Closure document link already on file for this project
    (see ProjectLinkDocument, reused as-is -- no new per-item linkage),
    or an explicit override. Deliberately project-scoped, not
    per-item: there's no field linking a ProjectLinkDocument to the
    specific activity/permit/task it's evidence for, so this checks
    "does at least one Project Closure link exist for this project",
    not "for this exact item" -- coarser than ideal, but real backend
    enforcement without inventing a linkage model nothing else needs."""
    if override_no_document:
        return
    has_document = (
        db.query(ProjectLinkDocument)
        .filter(
            ProjectLinkDocument.project_id == project.id,
            ProjectLinkDocument.category == "Project Closure",
            ProjectLinkDocument.deleted_at.is_(None),
        )
        .first()
        is not None
    )
    if not has_document:
        raise ValidationAppError(
            "Add a Project Closure document link as proof before marking this complete, "
            "or check the override box to confirm without one."
        )


def _assert_design_tasks_complete(db: Session, activity_id: int) -> None:
    """Gates marking a Design activity Complete (never Cancelled -- a
    descoped activity doesn't need its tasks finished) on every task
    linked to it (Task.selected_activity_id) already being Completed.
    An activity with no linked tasks at all passes through -- nothing
    to wait on. Unlike _assert_completion_evidence just below, this has
    no override: task completion is a real, load-bearing signal (it's
    also what maybe_auto_close_design_activity uses to close the
    activity automatically), not a paperwork formality, so it isn't
    something a checkbox should be able to skip past."""
    linked_tasks = (
        db.query(Task).filter(Task.selected_activity_id == activity_id, Task.deleted_at.is_(None)).all()
    )
    if any(task.status != "Completed" for task in linked_tasks):
        raise ValidationAppError(
            "All tasks linked to this Design activity must be Completed before it can be marked Complete."
        )


def close_design_activity(
    db: Session, project_no: str, activity_id: int, new_status: str, user_id: int, override_no_document: bool = False,
) -> ProjectSelectedActivity:
    """Direct user action -- closes a Design activity. new_status is
    'Complete' or 'Cancelled' -- the latter for a descoped activity that
    was never going to be finished, so it stops blocking project
    completion without pretending it was actually done. Marking it
    Complete requires every linked task to already be Completed (see
    _assert_design_tasks_complete) -- this used to be independent of
    the task-driven auto-close below ("user has full control"), which
    let staff mark a Design service complete while its own tasks were
    still open. Also tries auto-advancing the stage (same as every
    other stage-completing action) -- closing the last open Design
    activity is exactly what Design's own exit criterion checks, so
    nothing should be left waiting on a separate manual "move stage"
    click that doesn't currently exist in the UI."""
    if new_status not in ("Complete", "Cancelled"):
        raise ValidationAppError("new_status must be 'Complete' or 'Cancelled'.")
    project = get_project(db, project_no)
    activity = get_selected_activity(db, project.id, activity_id)
    if new_status == "Complete":
        _assert_design_tasks_complete(db, activity.id)
        _assert_completion_evidence(db, project, override_no_document)
    _set_design_activity_status(db, activity, new_status, user_id, auto=False)
    db.flush()
    try_auto_advance_stage(db, project, user_id)
    db.commit()
    db.refresh(activity)
    return activity


def reopen_design_activity(db: Session, project_no: str, activity_id: int, user_id: int) -> ProjectSelectedActivity:
    """The other half of "user has full control" -- undoes a close
    (manual or auto-derived) regardless of what its linked tasks say."""
    project = get_project(db, project_no)
    activity = get_selected_activity(db, project.id, activity_id)
    if activity.status not in ("Complete", "Cancelled"):
        raise ValidationAppError("This activity isn't closed.")
    previous = activity.status
    activity.status = "In Progress"
    activity.closed_at = None
    activity.closed_by = None
    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Design activity reopened", user_id,
        previous_value=previous, new_value=activity.status,
    )
    db.commit()
    db.refresh(activity)
    return activity


def maybe_auto_close_design_activity(db: Session, activity_id: int, user_id: int) -> None:
    """Called by task_service.set_status whenever a task linked to a
    Design activity is marked Completed -- if every one of that
    activity's linked tasks (there must be at least one) is now
    Completed, closes the activity automatically. Never overrides a
    status already set by hand (Complete/Cancelled), and is a no-op
    for the common case of a task with no linked activity. Doesn't
    commit its own status change -- the caller's status-change
    transaction covers that too -- but the stage-advance check it may
    trigger (try_auto_advance_stage, which can itself reach Handover and
    fire the checklist/hand-over notice -- see _apply_stage_change) does
    commit its own work partway through; that's fine, it just means this
    call and the caller's own commit each cover part of the same
    overall change."""
    activity = db.query(ProjectSelectedActivity).filter(ProjectSelectedActivity.id == activity_id).first()
    if activity is None or activity.status in ("Complete", "Cancelled"):
        return
    linked_tasks = (
        db.query(Task)
        .filter(Task.selected_activity_id == activity_id, Task.deleted_at.is_(None))
        .all()
    )
    if not linked_tasks or any(task.status != "Completed" for task in linked_tasks):
        return
    _set_design_activity_status(db, activity, "Complete", user_id, auto=True)
    project = db.query(Project).filter(Project.id == activity.project_id).first()
    if project is not None:
        db.flush()
        try_auto_advance_stage(db, project, user_id)


def get_selected_permit(db: Session, project_id: int, permit_id: int) -> ProjectSelectedPermit:
    """A single Permit row, scoped to a specific project so a caller
    can't operate on another project's row just by knowing its raw
    id -- same reasoning as get_selected_activity above."""
    permit = (
        db.query(ProjectSelectedPermit)
        .filter(ProjectSelectedPermit.id == permit_id, ProjectSelectedPermit.project_id == project_id)
        .first()
    )
    if permit is None:
        raise NotFoundError("Selected permit")
    return permit


def maybe_auto_close_permit(db: Session, permit_id: int, user_id: int) -> None:
    """Same shape as maybe_auto_close_design_activity above, for Permits
    (migration 0088) -- called by task_service.set_status whenever a
    task linked to a permit is marked Completed. Never overrides a
    status already set by hand, a no-op for a permit with no linked
    tasks. Doesn't commit its own status change -- see
    maybe_auto_close_design_activity's docstring for why."""
    permit = db.query(ProjectSelectedPermit).filter(ProjectSelectedPermit.id == permit_id).first()
    if permit is None or permit.status in ("Complete", "Cancelled"):
        return
    linked_tasks = (
        db.query(Task).filter(Task.selected_permit_id == permit_id, Task.deleted_at.is_(None)).all()
    )
    if not linked_tasks or any(task.status != "Completed" for task in linked_tasks):
        return
    previous = permit.status
    permit.status = "Complete"
    permit.closed_at = datetime.now(timezone.utc)
    permit.closed_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, permit.project_id, "Permit auto-closed (all linked tasks completed)", user_id,
        previous_value=previous, new_value="Complete",
    )
    project = db.query(Project).filter(Project.id == permit.project_id).first()
    if project is not None:
        db.flush()
        try_auto_advance_stage(db, project, user_id)


def set_permit_status(
    db: Session, project_no: str, permit_id: int, new_status: str, user_id: int, override_no_document: bool = False,
) -> ProjectSelectedPermit:
    """Permits have no sub-tasks of their own status-wise -- the user
    can always set this directly at their own discretion ("permit stage
    completion updated by the user directly"), on top of the
    task-driven auto-close above, same "user has full control"
    philosophy as Design. new_status is 'In Progress', 'Complete', or
    'Cancelled' (enforced by SetPermitStatusRequest) -- 'Eligible' is
    computed, not settable here (see _recompute_permit_eligibility)."""
    project = get_project(db, project_no)
    if new_status == "Complete":
        _assert_completion_evidence(db, project, override_no_document)
    permit = get_selected_permit(db, project.id, permit_id)
    previous = permit.status
    permit.status = new_status
    if new_status in ("Complete", "Cancelled"):
        permit.closed_at = datetime.now(timezone.utc)
        permit.closed_by = user_id
    else:
        permit.closed_at = None
        permit.closed_by = None
    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Permit status changed", user_id,
        previous_value=previous, new_value=new_status,
    )
    if new_status in ("Complete", "Cancelled"):
        _auto_complete_linked_tasks(db, Task.selected_permit_id == permit.id, user_id)
    db.commit()
    db.refresh(permit)
    try_auto_advance_stage(db, project, user_id)
    return permit


def get_selected_supervision_activity(
    db: Session, project_id: int, activity_id: int
) -> ProjectSelectedSupervisionActivity:
    """A single Supervision activity row, scoped to a specific project --
    same reasoning as get_selected_activity/get_selected_permit above."""
    activity = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(
            ProjectSelectedSupervisionActivity.id == activity_id,
            ProjectSelectedSupervisionActivity.project_id == project_id,
        )
        .first()
    )
    if activity is None:
        raise NotFoundError("Selected supervision activity")
    return activity


def maybe_auto_close_supervision_activity(db: Session, activity_id: int, user_id: int) -> None:
    """Same shape as maybe_auto_close_permit above, for Supervision
    activities (migration 0088). Doesn't commit its own status change --
    see maybe_auto_close_design_activity's docstring for why."""
    activity = (
        db.query(ProjectSelectedSupervisionActivity)
        .filter(ProjectSelectedSupervisionActivity.id == activity_id)
        .first()
    )
    if activity is None or activity.status in ("Complete", "Cancelled"):
        return
    linked_tasks = (
        db.query(Task)
        .filter(Task.selected_supervision_activity_id == activity_id, Task.deleted_at.is_(None))
        .all()
    )
    if not linked_tasks or any(task.status != "Completed" for task in linked_tasks):
        return
    previous = activity.status
    activity.status = "Complete"
    activity.closed_at = datetime.now(timezone.utc)
    activity.closed_by = user_id
    audit_service.log_event(
        db, ENTITY_TYPE, activity.project_id, "Supervision activity auto-closed (all linked tasks completed)",
        user_id, previous_value=previous, new_value="Complete",
    )
    project = db.query(Project).filter(Project.id == activity.project_id).first()
    if project is not None:
        db.flush()
        try_auto_advance_stage(db, project, user_id)


def set_supervision_status(
    db: Session, project_no: str, activity_id: int, new_status: str, user_id: int, override_no_document: bool = False,
) -> ProjectSelectedSupervisionActivity:
    """Supervision has no sub-tasks of its own status-wise -- the user
    can always set this directly, based on their own read of the site
    engineer's reports, whenever they judge it done ("closes anytime as
    they deem fit"), on top of the task-driven auto-close above.
    new_status is 'In Progress', 'Complete', or 'Cancelled' -- 'Eligible'
    is computed, not settable here (see
    _recompute_supervision_eligibility). Same shape as
    set_permit_status."""
    project = get_project(db, project_no)
    if new_status == "Complete":
        _assert_completion_evidence(db, project, override_no_document)
    activity = get_selected_supervision_activity(db, project.id, activity_id)
    previous = activity.status
    activity.status = new_status
    if new_status in ("Complete", "Cancelled"):
        activity.closed_at = datetime.now(timezone.utc)
        activity.closed_by = user_id
    else:
        activity.closed_at = None
        activity.closed_by = None
    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Supervision activity status changed", user_id,
        previous_value=previous, new_value=new_status,
    )
    if new_status in ("Complete", "Cancelled"):
        _auto_complete_linked_tasks(db, Task.selected_supervision_activity_id == activity.id, user_id)
    db.commit()
    db.refresh(activity)
    try_auto_advance_stage(db, project, user_id)
    return activity


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
        if supervision_end_date is not None and activity.endDate > supervision_end_date:
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


def _persist_permit_selection(db: Session, project_id: int, selection: list) -> None:
    """Inserts one ProjectSelectedPermit row per picked permit
    (PermitPickerDialog, New Project Wizard's Permits step) --
    permitId is the catalog's display id ("PER-003"), resolved to the
    real catalog row so eligibility checks
    (_recompute_permit_eligibility) can join against
    PermitPrerequisite; permit_name is still captured as an immutable
    snapshot for display, same as ProjectSelectedActivity/
    ProjectSelectedSupervisionActivity."""
    for permit in selection:
        catalog_item = permit_catalog_service.get_permit(db, permit.permitId)
        db.add(
            ProjectSelectedPermit(
                project_id=project_id,
                permit_catalog_item_id=catalog_item.id,
                permit_name=permit.permitName,
                permit_price=catalog_item.fixed_cost,
            )
        )


def add_selected_services(
    db: Session,
    project_no: str,
    design_activities: list,
    supervision_activities: list,
    supervision_start_date,
    supervision_end_date,
    user_id: int | None,
) -> Project:
    """Lets staff add more billable Design and/or Supervision activities
    to a project at any point in its lifecycle -- selections used to be
    fixed forever at creation (see ServicePickerDialog.vue), which meant
    a Design-only project had no way to ever pick up Supervision work
    (or additional Design work) later. Only genuinely new activities (by
    activityId, not already selected) are inserted; existing rows are
    left untouched.

    Deliberately does NOT create a quotation/agreement/contract itself --
    once the new activities exist here, includesDesign/includesSupervision
    (compute_stage_flags) picks them up automatically, and staff cover the
    newly billable work with an ordinary "New Quotation" / "New Contract" /
    "Create Payment Plan" action, exactly like the project's original
    services were -- all three already support more than one row per
    project (Quotation and Contract have no cardinality limit at all;
    FinancialAgreement only blocks a *second* agreement for a stream that
    already has one, which doesn't apply to a stream being billed for the
    first time)."""
    project = get_project(db, project_no)
    assert_project_open_for_new_work(project)

    existing_design_ids = {a.activity_id for a in get_selected_activities(db, project.id)}
    existing_supervision_ids = {a.activity_id for a in get_selected_supervision_activities(db, project.id)}
    new_design = [a for a in design_activities if a.activityId not in existing_design_ids]
    new_supervision = [a for a in supervision_activities if a.activityId not in existing_supervision_ids]

    if not new_design and not new_supervision:
        raise ValidationAppError("Every selected activity is already part of this project.")

    for activity in new_design:
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
    if new_design:
        project.service_total = float(project.service_total or 0) + sum(float(a.fixedCost) for a in new_design)

    if new_supervision and project.supervision_start_date is None:
        # First-ever Supervision activity for this project -- same
        # requirement create_project enforces up front.
        if supervision_start_date is None:
            raise ValidationAppError("supervisionStartDate is required when adding Supervision activities for the first time.")
        project.supervision_start_date = supervision_start_date
        project.supervision_end_date = supervision_end_date

    added_monthly = _persist_supervision_selection(
        db, project.id, new_supervision, project.supervision_start_date, project.supervision_end_date,
    )
    if added_monthly:
        project.supervision_monthly_total = float(project.supervision_monthly_total or 0) + added_monthly

    added_names = ", ".join(a.activityName for a in [*new_design, *new_supervision])
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Services added", user_id, new_value=added_names)
    timeline_service.create_system_event(
        db, project.id, "note", title="Additional services added", description=added_names, actor_id=user_id,
    )

    # Services added here bypass the one-time "leaving Contract"
    # transition that normally auto-generates each activity's task (see
    # _apply_stage_change/_create_service_tasks) -- that hook only ever
    # fires once per project, but this function explicitly lets staff
    # add more Design/Supervision activities "at any point in its
    # lifecycle", including long after Contract was left. Without this
    # call, an activity added here would sit with no linked task at all,
    # silently breaking the "every Design activity gets a task" plan and
    # the auto-close behavior that depends on it (maybe_auto_close_design_
    # activity / _assert_design_tasks_complete). Idempotent against
    # activities/permits already covered by an earlier call, so this is
    # safe even if some of what's selected already has tasks.
    db.flush()
    _create_service_tasks(db, project, user_id)

    db.commit()
    db.refresh(project)
    return project


def compute_stage_flags(
    selected_activities: list, selected_supervision_activities: list, selected_permits: list,
) -> tuple[bool, bool, bool]:
    """(includes_design, includes_government_submission, includes_supervision)
    -- whether this project's workflow should offer a Design/Government
    Submission (Permits, shown as "Approvals & Permits")/Supervision
    stage each (see WORKFLOW_STAGES). All three are independent,
    parallel tracks off Contract (migration 0089) -- a project with none
    of a given track's items selected skips that branch entirely, same
    as Design/Supervision already did before Government Submission
    joined them as conditional too. Deterministic since migration 0059:
    Design/Supervision services are different catalog branches and
    Permits their own selection, so which rows exist says everything --
    no name-matching against category/service names."""
    return (len(selected_activities) > 0, len(selected_permits) > 0, len(selected_supervision_activities) > 0)


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
        site_address=payload.siteAddress,
        client_id=client.id,
        service=payload.service,
        engineer_id=engineer.id,
        priority=payload.priority,
        start_date=payload.startDate,
        target_date=payload.targetDate,
        service_total=service_total,
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

    _persist_permit_selection(db, project.id, payload.selectedPermits or [])
    db.flush()
    # Picks up any permit/supervision activity with no prerequisites at
    # all (immediately eligible) -- this is the only call site that
    # fires for a project with no Design activities to ever close and
    # trigger the recompute from _set_design_activity_status instead.
    _recompute_permit_eligibility(db, project)
    _recompute_supervision_eligibility(db, project)

    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project created", user_id, new_value=project.project_name)
    db.commit()
    db.refresh(project)

    _send_project_created_email(db, client, project, engineer)
    return project


def _send_project_created_email(db: Session, client: Client, project: Project, engineer: User) -> None:
    """Purely informational -- unlike onboarding's OTP email, nothing
    about project creation depends on the client ever seeing this, so a
    failed/unconfigured send must never fail project creation itself
    (same "degrade gracefully" idea as ai_service's identification
    check). Only sent when the client has actually consented to email --
    email_consent is the one flag every messaging feature should check
    before writing to a client."""
    if not client.email_consent:
        return
    try:
        subject, body = email_template_service.render(
            db,
            "project_created",
            {
                "contact_person": client.contact_person,
                "company_name": client.company_name,
                "project_name": project.project_name,
                "project_no": project.project_no,
                "service": project.service,
                "site_address_line": f"Site address: {project.site_address}\n" if project.site_address else "",
                "start_date": project.start_date.isoformat(),
                "target_date": project.target_date.isoformat(),
                "engineer_name": engineer.full_name,
            },
        )
        email_service.send_email(client.email, subject, body, db=db)
    except ValidationAppError:
        pass


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
    if payload.siteAddress is not None:
        new_site_address = payload.siteAddress.strip() or None
        if new_site_address != project.site_address:
            changes["site_address"] = (project.site_address, new_site_address)
        project.site_address = new_site_address
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
        # A pushed-out target_date may no longer be in the past --
        # check_and_notify_overdue_projects only re-notifies once this
        # is cleared, the same "cleared the moment the underlying
        # condition stops being true" rule stale_notified_at follows.
        if project.overdue_notified_at is not None and payload.targetDate >= date.today():
            project.overdue_notified_at = None
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
    """See docs/PROJECT_WORKFLOW_MAP for the source diagram (migration
    0089). Requirement -> Quotation -> Payment Plan -> Contract is a
    straight line for every project; from Contract, Design, Government
    Submission (Permits, shown as "Approvals & Permits"), and
    Supervision become independent PARALLEL tracks -- a project skips
    whichever of the three it has no selected items for (see
    compute_stage_flags), and the three impose no ordering on each
    other (PROJECT_STAGE_ALLOWED_TRANSITIONS lets any of them move
    freely to any other, purely a "which view is focused" pointer, not
    a real gate). All three converge on Handover, which requires every
    included track to be Complete/Cancelled (and, for Government
    Submission specifically, at least one Approved submission on file --
    you can't hand over a permit that was never actually granted) --
    that unified check is the "elif new_stage == 'Handover'" branch
    below, replacing what used to be two different sequential per-hop
    checks (Design's own exit, then Government Submission's into
    Supervision) back when the three were still a fixed chain.

    Payment Plan (migration 0061) requires an Approved quotation to
    enter (moved here from Contract's own entry criterion -- Contract
    is now only reachable via Payment Plan, so checking it there instead
    is equivalent and no longer needs re-checking a second time on the
    way into Contract), and requires every included stream's financial
    agreement to exist AND be Approved before leaving into Contract
    (strengthened from Contract's own former exit criterion, which only
    checked existence -- see FinancialAgreement.status). Permits have no
    financial agreement of their own (AgreementStream is Design/
    Supervision only), so they're not part of that check.
    """
    if new_stage in ("Design", "Government Submission", "Supervision"):
        includes_design, includes_government_submission, includes_supervision = compute_stage_flags(
            get_selected_activities(db, project.id),
            get_selected_supervision_activities(db, project.id),
            get_selected_permits(db, project.id),
        )
        if new_stage == "Design" and not includes_design:
            raise ValidationAppError(
                "This project's selected services/activities don't include Design work -- "
                "there's no Design stage for it to move into."
            )
        if new_stage == "Government Submission" and not includes_government_submission:
            raise ValidationAppError(
                "This project has no Permits selected -- there's no Approvals & Permits stage for it to move into."
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
        # There's no client-facing sign-off gating this transition
        # anymore -- the project associate confirms the scope is final
        # and moves it into Quotation directly (see
        # confirm_requirement_scope, called by ProjectRequirementTab.vue's
        # "Confirm" button) once there's an actual scope to quote
        # against.
        if not (project.description or "").strip():
            problems.append("the scope of work written up")

    elif new_stage == "Payment Plan":
        # Moved here from Contract's own former entry criterion --
        # Contract is now only reachable via Payment Plan (see
        # PROJECT_STAGE_ALLOWED_TRANSITIONS), so checking it on the way
        # into Payment Plan is equivalent and Contract itself no longer
        # needs to re-check it (Quotation.status can't be un-approved
        # once set -- QUOTATION_ALLOWED_TRANSITIONS has no path out of
        # "Approved" -- so the fact stays true transitively).
        approved_quotation = (
            db.query(Quotation)
            .filter(Quotation.project_id == project.id, Quotation.status == "Approved", Quotation.deleted_at.is_(None))
            .first()
        )
        if approved_quotation is None:
            problems.append("an Approved quotation")

    elif previous_stage == "Payment Plan":
        # Gates leaving Payment Plan for Contract -- every included
        # stream's financial agreement (payment dates, amount, schedule)
        # has to exist AND be explicitly Approved, not merely created.
        # Checked per stream (migration 0059) -- a project that includes
        # both Design and Supervision needs both agreements approved,
        # not just one. Only approval is required here, not that it's
        # fully paid -- payment is expected to happen across the
        # project's lifetime, tracked by the reminder job below.
        includes_design, _, includes_supervision = compute_stage_flags(
            get_selected_activities(db, project.id),
            get_selected_supervision_activities(db, project.id),
            get_selected_permits(db, project.id),
        )
        if includes_design:
            design_agreement = payment_service.get_agreement_by_project(db, project.project_no, "Design")
            if design_agreement is None:
                problems.append("a Design financial agreement (payment dates and amount)")
            elif design_agreement.status != "Approved":
                problems.append("the Design financial agreement approved")
        if includes_supervision:
            supervision_agreement = payment_service.get_agreement_by_project(db, project.project_no, "Supervision")
            if supervision_agreement is None:
                problems.append("a Supervision financial agreement (payment dates and amount)")
            elif supervision_agreement.status != "Approved":
                problems.append("the Supervision financial agreement approved")

    # Not part of the if/elif chain above -- these two are independent
    # conditions on previous_stage and new_stage respectively, and both
    # have to apply together for a project with none of Design/
    # Government Submission/Supervision selected, whose only forward
    # target from Contract is Handover directly (see
    # _auto_advance_target's "return 'Handover'" fallback): it still
    # needs a signed contract on file (nothing else checks that for
    # such a project) *and* every task closed (the Handover branch
    # below), not just one or the other. An elif here used to let
    # whichever came first win, silently skipping the other.
    if previous_stage == "Contract":
        # Gates leaving Contract into whichever of Design/Government
        # Submission/Supervision is actually next for this project (see
        # _auto_advance_target) -- a contract has to actually be signed,
        # not merely exist as a Draft -- this is what "Documents Signed"
        # means in practice (the separate documents_signed
        # approval-process gate used to be checked here instead, but
        # that's a second, easy-to-forget manual upload nothing else in
        # the flow prompts anyone to do; the contract's own status is
        # the real, already-visible signal for this).
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

    if new_stage == "Handover":
        # The convergence gate for all three parallel tracks -- every
        # one this project actually includes has to be fully closed
        # (used to be two different sequential per-hop checks, Design's
        # own exit and Government Submission's into Supervision, back
        # when they were still a fixed chain; now it's one unified
        # AND-gate, checked once regardless of which of the three
        # previous_stage happens to be). Reaching Handover at all is
        # what _apply_stage_change's own Handover-entry hook treats as
        # "ready" -- generating the checklist and notifying staff -- so
        # this is the one place that readiness is actually decided.
        includes_design, includes_government_submission, includes_supervision = compute_stage_flags(
            get_selected_activities(db, project.id),
            get_selected_supervision_activities(db, project.id),
            get_selected_permits(db, project.id),
        )
        if includes_design:
            unfinished_activities = [
                a for a in get_selected_activities(db, project.id) if a.status not in ("Complete", "Cancelled")
            ]
            if unfinished_activities:
                problems.append(
                    f"every Design activity closed ({len(unfinished_activities)} still open: "
                    f"{', '.join(a.activity_name for a in unfinished_activities)})"
                )
        if includes_government_submission:
            # Symmetric with Design/Supervision just below/above --
            # every selected Permit's own status (Complete/Cancelled) is
            # the authoritative "is this done" signal, same as an
            # activity's. This used to also require a GovernmentSubmission
            # row on file with status Approved, but Permits have no
            # sub-tasks and no other gate gating "Complete" (see
            # set_permit_status -- staff can close a permit by hand,
            # e.g. an authority approval obtained and evidenced outside
            # this system's own Submission tracking), so that extra
            # check could block Handover indefinitely on a permit
            # everyone -- including this exit criterion's own "every
            # Permit closed" check just above -- already agrees is done,
            # with no visible link telling staff what to do about it.
            unfinished_permits = [
                p for p in get_selected_permits(db, project.id) if p.status not in ("Complete", "Cancelled")
            ]
            if unfinished_permits:
                problems.append(
                    f"every Permit closed ({len(unfinished_permits)} still open: "
                    f"{', '.join(p.permit_name for p in unfinished_permits)})"
                )
        if includes_supervision:
            unfinished_supervision = [
                a for a in get_selected_supervision_activities(db, project.id) if a.status not in ("Complete", "Cancelled")
            ]
            if unfinished_supervision:
                problems.append(
                    f"every Supervision activity closed ({len(unfinished_supervision)} still open: "
                    f"{', '.join(a.activity_name for a in unfinished_supervision)})"
                )
        # An activity/permit can be force-closed by a human even while a
        # task under it (or a generic, unlinked one) is still open, so
        # this is a separate check, not implied by the ones above:
        # nothing on the project's to-do list should be left dangling
        # once it's handed over.
        open_tasks = (
            db.query(Task)
            .filter(Task.project_id == project.id, Task.deleted_at.is_(None), Task.status != "Completed")
            .all()
        )
        if open_tasks:
            problems.append(
                f"every task closed ({len(open_tasks)} still open: "
                f"{', '.join(t.title for t in open_tasks)})"
            )

    if problems:
        raise ValidationAppError(
            f"Cannot move this project to '{new_stage}' yet -- missing: {'; '.join(problems)}."
        )


# --- workflow stage / progress -- merged so "how far along is this
# project" is always one consistent story instead of two independently
# maintained numbers. Weighted by what's actually been delivered, not an
# even split across stages: Requirement/Quotation/Payment Plan earn
# nothing (there's no signed commitment yet to measure progress
# against) -- Contract signed is the first real milestone, worth 10%.
# The three parallel tracks (Design/Government Submission/Supervision,
# migration 0089) share 40% equally among however many of them this
# project actually includes -- they're parallel, not sequential, so
# there's no single "how far through them" position, only each one's own
# fraction of its selected items Complete/Cancelled. Payment received
# (across every financial agreement on the project) is worth another
# 40%. The last 10% is Handover -- but rather than a partial credit for
# merely reaching that stage, it's folded into the status == "Completed"
# shortcut below, so 100% and "the client's signed acknowledgment is in"
# are the same moment, not two different ways of saying "done".
def _track_completion_fraction(items: list) -> float:
    if not items:
        return 0.0
    done = sum(1 for item in items if item.status in ("Complete", "Cancelled"))
    return done / len(items)


def recompute_progress(db: Session, project: Project) -> int:
    """Does not commit -- callers already do."""
    if project.status == "Completed":
        project.progress = 100
        return project.progress

    if project.current_stage in ("Requirement", "Quotation", "Payment Plan", "Contract"):
        project.progress = 0
        return project.progress

    # Past Contract means it's already signed -- PROJECT_STAGE_ALLOWED_
    # TRANSITIONS has no path back into "Contract", and leaving it in
    # the first place already required a signed/active Contract on file
    # (see _assert_stage_exit_criteria's "previous_stage == Contract"
    # branch) -- so reaching here at all is exactly "contract completed".
    progress = 10.0

    selected_activities = get_selected_activities(db, project.id)
    selected_permits = get_selected_permits(db, project.id)
    selected_supervision_activities = get_selected_supervision_activities(db, project.id)
    includes_design, includes_government_submission, includes_supervision = compute_stage_flags(
        selected_activities, selected_supervision_activities, selected_permits,
    )
    included_track_count = sum((includes_design, includes_government_submission, includes_supervision))
    if included_track_count > 0:
        track_weight = 40 / included_track_count
        if includes_design:
            progress += track_weight * _track_completion_fraction(selected_activities)
        if includes_government_submission:
            progress += track_weight * _track_completion_fraction(selected_permits)
        if includes_supervision:
            progress += track_weight * _track_completion_fraction(selected_supervision_activities)

    total_contract_amount = (
        db.query(func.sum(FinancialAgreement.contract_amount))
        .filter(FinancialAgreement.project_id == project.id)
        .scalar()
        or 0
    )
    if total_contract_amount > 0:
        total_received = (
            db.query(func.sum(Payment.amount_received)).filter(Payment.project_id == project.id).scalar() or 0
        )
        progress += 40 * min(float(total_received) / float(total_contract_amount), 1.0)

    project.progress = max(0, min(100, round(progress)))
    return project.progress


def _auto_advance_target(
    current_stage: str, includes_design: bool, includes_government_submission: bool, includes_supervision: bool,
) -> str | None:
    """The one valid next stage for this project once its exit criteria
    (_assert_stage_exit_criteria) are met, so firing it automatically
    doesn't remove a real choice from anyone -- it just saves the
    separate manual click after the condition that already gates it
    becomes true (approving a quotation, approving a financial
    agreement, signing a contract, closing the last item on a track).

    Design, Government Submission, and Supervision (migration 0089) are
    parallel, not sequential -- once in Contract, this heads for
    whichever of the three the project actually includes, arbitrarily
    picking the first (there's no ordering between them, that's just
    where current_stage's pointer lands); once sitting on any one of
    the three, the only forward target is Handover, and
    _assert_stage_exit_criteria's own Handover branch is what actually
    decides whether every included track is done -- this function
    doesn't duplicate that check, it just always proposes Handover and
    lets the exit criteria silently reject it (via
    try_auto_advance_stage's own try/except) until they're satisfied. A
    project with none of the three tracks at all heads straight to
    Handover from Contract, nothing to converge on. Reopening (Handover
    back to one of the three) stays manual -- an exceptional,
    reason-required correction, not something that should ever happen
    as a side effect of an unrelated action.

    Requirement -> Quotation is likewise never listed here: unlike
    every other transition below, there's no other business event to
    hook this one onto -- it's the sole outcome of
    confirm_requirement_scope's own explicit "Confirm" action, which
    applies that stage change directly instead of going through this
    function. Were "Quotation" returned here, some unrelated action
    that merely happens to satisfy Quotation's exit criteria (e.g.
    adding the client's identification once a scope is already saved)
    would silently advance the project without anyone having clicked
    Confirm."""
    if current_stage == "Quotation":
        return "Payment Plan"
    if current_stage == "Payment Plan":
        return "Contract"
    if current_stage == "Contract":
        if includes_design:
            return "Design"
        if includes_government_submission:
            return "Government Submission"
        if includes_supervision:
            return "Supervision"
        return "Handover"
    if current_stage in ("Design", "Government Submission", "Supervision"):
        return "Handover"
    return None


_SERVICE_TASK_DUE_TIME = time(17, 0)


def _create_service_tasks(db: Session, project: Project, user_id: int | None) -> None:
    """Auto-generates one Task per selected Design activity, Permit, and
    Supervision activity the moment the project leaves Contract (see
    _apply_stage_change) -- Design, Government Submission (Permits), and
    Supervision all become active, parallel tracks at once from here, so
    their tracked to-dos are created together rather than staggered by
    whichever stage the project's current_stage literal happens to sit
    on. Assigned to the project's own engineer, spanning the project's
    own start_date/target_date -- staff can reassign the owner or either
    date on any of them afterward (see task_service.update_task). Starts
    life as 'Preset' (see TASK_STATUSES) rather than a manually-created
    task's 'Pending' default, until touched -- the UI flags a task still
    sitting in 'Preset' to prompt review instead of silently leaving it
    on the original engineer/dates forever.

    Idempotent per selected item -- skips any that already has a linked
    task (so a re-entry into this can't happen, since Contract is only
    ever left once per project, doesn't double them up) and any already
    Complete/Cancelled (nothing to do)."""
    existing_activity_ids = {
        row[0] for row in db.query(Task.selected_activity_id).filter(
            Task.project_id == project.id, Task.deleted_at.is_(None), Task.selected_activity_id.isnot(None),
        ).all()
    }
    existing_permit_ids = {
        row[0] for row in db.query(Task.selected_permit_id).filter(
            Task.project_id == project.id, Task.deleted_at.is_(None), Task.selected_permit_id.isnot(None),
        ).all()
    }
    existing_supervision_ids = {
        row[0] for row in db.query(Task.selected_supervision_activity_id).filter(
            Task.project_id == project.id, Task.deleted_at.is_(None), Task.selected_supervision_activity_id.isnot(None),
        ).all()
    }

    def _add_task(title: str, **link: int) -> None:
        task = Task(
            task_no=next_task_number(db, project.id, project.project_no),
            project_id=project.id,
            title=title,
            assigned_to=project.engineer_id,
            start_date=project.start_date,
            due_date=project.target_date,
            due_time=_SERVICE_TASK_DUE_TIME,
            status="Preset",
            **link,
        )
        db.add(task)
        db.flush()
        notification_service.create_notification(
            db, project.engineer_id, "New task assigned", f"You've been assigned: {title}", "Task",
            link_route_name="tasks",
        )

    created_count = 0

    for activity in get_selected_activities(db, project.id):
        if activity.id in existing_activity_ids or activity.status in ("Complete", "Cancelled"):
            continue
        _add_task(activity.activity_name, selected_activity_id=activity.id)
        created_count += 1

    for permit in get_selected_permits(db, project.id):
        if permit.id in existing_permit_ids or permit.status in ("Complete", "Cancelled"):
            continue
        _add_task(permit.permit_name, selected_permit_id=permit.id)
        created_count += 1

    for activity in get_selected_supervision_activities(db, project.id):
        if activity.id in existing_supervision_ids or activity.status in ("Complete", "Cancelled"):
            continue
        _add_task(activity.activity_name, selected_supervision_activity_id=activity.id)
        created_count += 1

    # Only log when this call actually generated something -- it's now
    # called both at the one-time Contract exit (see _apply_stage_change)
    # and again whenever add_selected_services adds more activities to a
    # project later (idempotent either way, via the existing_*_ids skips
    # above), and the second caller frequently has nothing new to create
    # (e.g. only Supervision was added and every Design activity already
    # has a task). A no-op "Service tasks created" audit entry would be
    # actively misleading in that case.
    if created_count:
        audit_service.log_event(db, ENTITY_TYPE, project.id, "Service tasks created", user_id)


def _apply_stage_change(
    db: Session, project: Project, new_stage: str, reason: str | None, user_id: int | None, event_label: str = "Stage changed"
) -> None:
    previous_stage = project.current_stage
    audit_service.log_event(
        db, ENTITY_TYPE, project.id, event_label, user_id,
        previous_value=previous_stage, new_value=new_stage, reason=reason,
    )
    project.current_stage = new_stage
    if previous_stage == "Contract":
        # The one and only time a project ever leaves Contract (see
        # PROJECT_STAGE_ALLOWED_TRANSITIONS -- there's no path back into
        # it) -- Design, Government Submission (Permits), and Supervision
        # all become active, parallel tracks from here, whichever of
        # them this project actually includes (new_stage is just
        # whichever one _auto_advance_target picked to land on first;
        # _create_service_tasks itself covers every included track
        # regardless of which one that was).
        _create_service_tasks(db, project, user_id)
    if new_stage == "Handover":
        # Design, Government Submission (Permits), and Supervision all
        # converge here -- reaching this stage at all already means
        # _assert_stage_exit_criteria's Handover branch confirmed every
        # included track is closed, so there's nothing left to check;
        # this just generates the (idempotent) hand-over checklist and
        # notifies Administrators it's ready for the manual payment
        # confirmation + signed acknowledgment steps (see
        # confirm_handover_payment/confirm_project_handover below).
        _generate_handover_checklist(db, project)
        db.flush()
        try:
            notify_handover_ready(db, project.project_no, user_id)
        except ValidationAppError:
            # This project's client record is missing -- handover_sent_at
            # stays unset; staff can retry via the manual re-notify path
            # once that's fixed.
            pass
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


def get_stage_eligibility(db: Session, project_no: str) -> list[dict]:
    """One source of truth for "can this project move to stage X right
    now, and if not, why" -- reuses _assert_stage_exit_criteria itself
    (a pure check, no writes) rather than a second copy of the same
    rules, so the Stage dialog can show real-time eligibility instead of
    only failing after the fact on submit. Structurally-impossible
    targets (Design/Government Submission/Supervision when the project
    doesn't include that kind of work) are left out entirely rather than
    reported as ineligible -- same "don't even offer it" behavior the
    dialog already had via includesDesign/includesSupervision, just
    computed once here instead of duplicated on the frontend.
    """
    project = get_project(db, project_no)
    includes_design, includes_government_submission, includes_supervision = compute_stage_flags(
        get_selected_activities(db, project.id),
        get_selected_supervision_activities(db, project.id),
        get_selected_permits(db, project.id),
    )

    results: list[dict] = []
    for candidate in sorted(PROJECT_STAGE_ALLOWED_TRANSITIONS.get(project.current_stage, set())):
        if candidate == "Design" and not includes_design:
            continue
        if candidate == "Government Submission" and not includes_government_submission:
            continue
        if candidate == "Supervision" and not includes_supervision:
            continue
        try:
            _assert_stage_exit_criteria(db, project, project.current_stage, candidate)
        except ValidationAppError as error:
            results.append({"stage": candidate, "eligible": False, "reason": str(error)})
        else:
            results.append({"stage": candidate, "eligible": True, "reason": None})
    return results


def set_stage(db: Session, project_no: str, new_stage: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    previous_stage = project.current_stage
    assert_transition_allowed(
        PROJECT_STAGE_ALLOWED_TRANSITIONS, previous_stage, new_stage, "project"
    )
    _assert_stage_exit_criteria(db, project, previous_stage, new_stage)
    if new_stage in PROJECT_STAGE_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_stage}'.")
    # Reopening one of the three parallel tracks after Handover is a
    # correction -- can't live in the target-only REQUIRING_REASON table
    # above, since that only keys on the target state, not where the
    # transition came from, and Design/Government Submission/Supervision
    # are also each other's normal, reason-free lateral targets (moving
    # focus between peer tracks isn't a "reopening" of anything).
    if previous_stage == "Handover" and new_stage in ("Design", "Government Submission", "Supervision"):
        assert_reason_given(reason, "A reason is required to reopen this project's tracks after Handover.")

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
    includes_design, includes_government_submission, includes_supervision = compute_stage_flags(
        get_selected_activities(db, project.id),
        get_selected_supervision_activities(db, project.id),
        get_selected_permits(db, project.id),
    )
    target_stage = _auto_advance_target(
        project.current_stage, includes_design, includes_government_submission, includes_supervision,
    )
    if target_stage is None:
        return
    try:
        assert_transition_allowed(PROJECT_STAGE_ALLOWED_TRANSITIONS, project.current_stage, target_stage, "project")
        _assert_stage_exit_criteria(db, project, project.current_stage, target_stage)
    except AppError:
        # Not yet eligible (ValidationAppError, the expected/common case)
        # or the proposed target isn't a transition this table allows
        # right now (ConflictError) -- either way this is a best-effort
        # "advance it if it's ready" check, never something the caller's
        # own unrelated action should fail because of. Catching the
        # narrower ValidationAppError alone let a ConflictError from
        # assert_transition_allowed escape uncaught (see
        # PROJECT_STAGE_ALLOWED_TRANSITIONS' own comment on the Contract
        # -> Handover case that used to hit exactly this).
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


def _assert_requirement_editable(db: Session, project: Project) -> None:
    """The Requirement stage's own scope-of-work text stays editable all
    the way through quotation negotiation -- finalizing and even sending
    a quotation doesn't lock it, since the client may still come back
    asking for scope changes before they accept. It only freezes once a
    quotation has actually been Approved (see quotation_service.
    confirm_quotation_approval, the only path to that status): at that point
    the client has accepted both the scope and what it costs, and
    editing the scope afterward would silently invalidate what they
    just signed off on. Checked here rather than only on the frontend so
    a direct API call can't bypass it either, same convention as every
    other lock in this app (Quotation/Contract content, Draft-only
    Payment Plan edits)."""
    has_approved_quotation = (
        db.query(Quotation)
        .filter(Quotation.project_id == project.id, Quotation.status == "Approved", Quotation.deleted_at.is_(None))
        .first()
        is not None
    )
    if has_approved_quotation:
        raise ValidationAppError(
            "The scope of work is locked -- this project's quotation has already been approved."
        )


def save_scope_of_work(
    db: Session,
    project_no: str,
    scope_text: str,
    summary: str | None,
    user_id: int,
    file: UploadFile | None = None,
) -> Project:
    """The Requirement stage's own scope-of-work editor. Every save here
    writes a project_scope_revisions row (R0, R1, ...) and clears any
    existing client confirmation -- a confirmation is a sign-off on
    specific text, not a status that should silently keep covering
    whatever the text becomes after further edits. See
    confirm_requirement_scope. The otp_* field resets below are now
    inert leftovers from the old OTP/signed-upload confirmation flows
    (nothing sets them anymore) -- harmless to keep clearing for any
    project whose row still carries a value from before this change."""
    project = get_project(db, project_no)
    _assert_requirement_editable(db, project)
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

    project.scope_client_confirmed_at = None
    project.otp_code_hash = None
    project.otp_expires_at = None
    project.otp_attempts = 0
    project.otp_sent_at = None

    audit_service.log_field_changes(
        db, ENTITY_TYPE, project.id, {"description": (previous_description, scope_text)}, user_id
    )
    db.commit()
    db.refresh(project)
    return project


def confirm_requirement_scope(db: Session, project_no: str, user_id: int) -> Project:
    """The staff-side action that moves a project from Requirement into
    Quotation -- previously required the client's signed confirmation of
    the scope, uploaded here as a PDF; that client-facing step is gone,
    so this is now a direct action the project associate takes
    themselves once the scope is finalized, no upload or code involved.
    Still seeds scope_client_confirmed_at (reusing
    _assert_stage_exit_criteria's own Quotation checks, so this fails
    with the same messages get_stage_eligibility already surfaces) --
    quotation_service.confirm_quotation_approval keys its own "scope
    reconfirmed since last edit" section off that same timestamp, so
    this keeps that logic meaningful. Applies the Quotation stage
    change directly (via _apply_stage_change) rather than through
    try_auto_advance_stage/_auto_advance_target -- this is the only
    trigger for that transition (see _auto_advance_target's own
    comment on why Requirement is deliberately left out of it), so
    there's no "maybe some other action already got here first" case
    to silently no-op on. The client is still sent an FYI copy of the
    finalized scope (see requirement_confirmed's wording, updated by
    migration 0082 to no longer thank the client for "confirming" it
    themselves) -- a failed/unconfigured send only notifies
    Administrators, same as every other confirmation email in this
    app, never blocking the action itself."""
    project = get_project(db, project_no)
    if project.current_stage != "Requirement":
        raise ValidationAppError("This project has already moved past the Requirement stage.")
    _assert_stage_exit_criteria(db, project, project.current_stage, "Quotation")

    project.scope_client_confirmed_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Scope of work confirmed", user_id)
    timeline_service.create_system_event(
        db, project.id, "note", title="Scope of work confirmed", description=project.description, actor_id=user_id,
    )
    _apply_stage_change(db, project, "Quotation", None, user_id)
    db.commit()
    db.refresh(project)

    client = db.query(Client).filter(Client.id == project.client_id).first()
    if client is not None and client.email_consent:
        try:
            subject, body = email_template_service.render(
                db,
                "requirement_confirmed",
                {
                    "contact_person": client.contact_person,
                    "project_name": project.project_name,
                    "project_no": project.project_no,
                    "scope_text": project.description or "",
                },
            )
            email_service.send_email(client.email, subject, body, db=db)
        except ValidationAppError as error:
            notification_service.notify_role(
                db, "Administrator",
                "Scope-confirmed email failed to send",
                f"Project {project.project_no}'s scope-confirmed email to the client failed: {error}",
                "System",
                link_route_name="project-workspace", link_params={"projectId": project.project_no},
            )
            db.commit()

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
    """Soft-deletes unconditionally -- deliberately NOT gated on how many
    quotations/contracts/tasks/documents/government submissions the
    project has. Nothing is removed from disk: every one of those child
    records stays exactly as it was, still reachable through the audit
    trail and _project_exists() above. The only thing this changes is
    that get_project()/list_projects() (and everything downstream that
    calls them) stop seeing this project at all, so it drops out of
    tracking, billing reminders, and stage-advancement immediately --
    see check_and_notify_payment_reminders' and check_and_expire_
    quotations' own deleted-project filters for the two places that
    would otherwise have kept acting on a "deleted" project's still-open
    financial records. Fully reversible via restore_project.

    A previous version of this blocked the delete entirely whenever any
    child record existed, on the theory that a soft-deleted project's
    real FK constraints never fire to protect against orphaned-looking
    records. That protection isn't needed for a soft delete (nothing is
    actually orphaned -- the rows are all still there, just hidden), and
    in practice it made routine archival impossible for any project that
    had ever been quoted or invoiced, which is nearly all of them.
    """
    project = get_project(db, project_no)
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project deleted", actor_id, previous_value=project.project_name)
    project.deleted_at = datetime.now(timezone.utc)
    db.commit()


def restore_project(db: Session, project_no: str, actor_id: int) -> Project:
    """Undoes delete_project -- clears deleted_at so the project is a
    normal, active record again (list_projects, get_project, and every
    other lookup start including it immediately). Doesn't touch
    project.status or current_stage: a project deleted mid-stage comes
    back exactly where it left off."""
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.isnot(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Deleted project")

    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project restored", actor_id, previous_value=project.project_name)
    project.deleted_at = None
    db.commit()
    db.refresh(project)
    return project


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


# --- project completion / hand-over -------------------------------------
#
# The three parallel tracks (Design, Government Submission/Permits,
# Supervision) each carry their own status independently, but converge
# on the real "Handover" workflow stage (migration 0089) once every
# track this project actually includes is Complete/Cancelled and every
# task on the project is Completed -- see _assert_stage_exit_criteria's
# Handover branch, which is the one place that AND-gate is checked now
# (reaching the stage at all already proves it). Payment is no longer a
# precondition to REACH Handover -- it's confirmed from inside it (see
# confirm_handover_payment below), required before the final step,
# confirm_project_handover (the client's signed hand-over
# acknowledgment), which is what actually flips project.status to
# "Completed".


def get_handover_readiness(db: Session, project: Project) -> tuple[bool, str | None]:
    """Whether this project could enter (or has already entered) the
    Handover stage right now, and -- if not -- exactly what's still
    open. A pure, non-raising read of the same _assert_stage_exit_
    criteria check try_auto_advance_stage itself relies on, so a
    project that isn't ready yet can be explained to staff (which
    Design activities/Permits/Supervision items/tasks are still open)
    instead of just showing an empty checklist with no reason why."""
    if project.current_stage == "Handover":
        return True, None
    try:
        _assert_stage_exit_criteria(db, project, project.current_stage, "Handover")
    except ValidationAppError as error:
        return False, str(error)
    return True, None


def refresh_handover_checklist(db: Session, project: Project) -> list[HandoverChecklistItem]:
    """Public wrapper around _generate_handover_checklist for callers
    outside this module (see api/projects.py's GET handover-status) --
    safe to call regardless of the project's actual current_stage,
    since it only ever adds a row for a Design activity/Permit/
    Supervision activity that is *currently* Complete. Calling this on
    every read of the hand-over tab (rather than only once, from
    _apply_stage_change's Handover-entry hook) is what lets the
    "Completed Services Checklist" reflect items closed after the
    project's last actual stage transition, instead of a stale
    snapshot frozen at whatever moment it was first generated."""
    checklist = _generate_handover_checklist(db, project)
    db.commit()
    return checklist


def _generate_handover_checklist(db: Session, project: Project) -> list[HandoverChecklistItem]:
    """One row per Complete (not Cancelled -- nothing to hand over on a
    descoped item) Design activity/Permit/Supervision activity.
    Idempotent by construction -- HandoverChecklistItem's unique
    constraint (project_id, source_type, source_id) means calling this
    more than once for the same project just no-ops on items that
    already have a row ("no repetitions"). Does not commit -- the
    caller already does. Returns every item (existing + newly created)
    so the hand-over email can list them all."""
    existing = {
        (item.source_type, item.source_id): item
        for item in db.query(HandoverChecklistItem).filter(HandoverChecklistItem.project_id == project.id).all()
    }
    sources: list[tuple[str, int, str, datetime | None]] = (
        [
            ("Design", a.id, a.activity_name, a.closed_at)
            for a in get_selected_activities(db, project.id) if a.status == "Complete"
        ]
        + [
            ("Permit", p.id, p.permit_name, p.closed_at)
            for p in get_selected_permits(db, project.id) if p.status == "Complete"
        ]
        + [
            ("Supervision", a.id, a.activity_name, a.closed_at)
            for a in get_selected_supervision_activities(db, project.id) if a.status == "Complete"
        ]
    )
    for source_type, source_id, title, closed_at in sources:
        key = (source_type, source_id)
        if key in existing:
            continue
        item = HandoverChecklistItem(
            project_id=project.id, source_type=source_type, source_id=source_id,
            title=title, completed_at=closed_at or datetime.now(timezone.utc),
        )
        db.add(item)
        existing[key] = item
    db.flush()
    return list(existing.values())


def notify_handover_ready(db: Session, project_no: str, user_id: int | None) -> Project:
    """Notifies Administrators that a project is ready for hand-over --
    reaching the Handover stage already means every included track is
    closed (see _assert_stage_exit_criteria). Normally called by
    _apply_stage_change the moment the project enters Handover; also
    directly callable as a manual re-notify action. Previously this
    emailed the client an OTP code to read back; now the next step is a
    manual one (staff confirm payment via confirm_handover_payment, then
    collect the client's signed hand-over acknowledgment and confirm it
    via confirm_project_handover below), so this only needs to tell
    staff to go do that -- there's no client-facing code to send.
    Requires the hand-over checklist to already exist (the Handover-entry
    hook in _apply_stage_change always generates it first)."""
    project = get_project(db, project_no)
    client = db.query(Client).filter(Client.id == project.client_id).first()
    if client is None:
        raise ValidationAppError("This project's client record is missing.")

    checklist = (
        db.query(HandoverChecklistItem)
        .filter(HandoverChecklistItem.project_id == project.id)
        .order_by(HandoverChecklistItem.source_type.asc(), HandoverChecklistItem.id.asc())
        .all()
    )
    checklist_text = "\n".join(f"- [{item.source_type}] {item.title}" for item in checklist) or "(no items)"

    project.handover_sent_at = datetime.now(timezone.utc)
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Hand-over readiness notice sent", user_id)
    db.commit()
    db.refresh(project)

    notification_service.notify_role(
        db, "Administrator",
        "Project ready for hand-over",
        f"Project {project.project_no} has every planned item closed and is fully paid -- collect the "
        f"client's signed hand-over acknowledgment and confirm it on the project.\n\n{checklist_text}",
        "Project",
        link_route_name="project-workspace", link_params={"projectId": project.project_no},
    )
    db.commit()
    return project


def confirm_handover_payment(db: Session, project_no: str, user_id: int | None) -> Project:
    """Manual attestation, from the Handover stage's Payment Confirmation
    tab, that this project's payment has been received in full --
    independent of (and not required to match) the automatic
    payment_service.get_project_payment_status() reading the same tab
    shows alongside it as reference: staff can confirm by hand even if
    obligation tracking is incomplete (e.g. a payment collected outside
    the system). Required before confirm_project_handover will accept
    the signed hand-over acknowledgment below.

    Deliberately gated on nothing else -- not the project's current
    stage, not any other track's completion. This is staff attesting a
    fact about money already received, which doesn't become less true
    just because some other Handover exit criterion (an open task, an
    unclosed track) hasn't cleared yet; requiring the project to already
    be sitting in "Handover" here only forced staff to wait on an
    unrelated blocker before they could even record a fact that's
    already true."""
    project = get_project(db, project_no)
    project.handover_payment_confirmed_at = datetime.now(timezone.utc)
    project.handover_payment_confirmed_by = user_id
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Hand-over payment confirmed", user_id)
    db.commit()
    db.refresh(project)
    return project


def unconfirm_handover_payment(db: Session, project_no: str, user_id: int | None) -> Project:
    """Undoes confirm_handover_payment -- e.g. confirmed by mistake, or
    before the final signed acknowledgment is uploaded."""
    project = get_project(db, project_no)
    if project.handover_payment_confirmed_at is None:
        raise ValidationAppError("Payment hasn't been confirmed for this project.")
    project.handover_payment_confirmed_at = None
    project.handover_payment_confirmed_by = None
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Hand-over payment confirmation undone", user_id)
    db.commit()
    db.refresh(project)
    return project


def update_handover_notes(db: Session, project_no: str, notes: str, user_id: int | None) -> Project:
    """Free-text closing remarks for the Handover stage's Notes and
    Report tab -- a single editable field, not a running log (see
    timeline_service for that)."""
    project = get_project(db, project_no)
    if project.current_stage != "Handover":
        raise ValidationAppError("This project hasn't reached the Handover stage yet.")
    project.handover_notes = notes
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Hand-over notes updated", user_id)
    db.commit()
    db.refresh(project)
    return project


def confirm_project_handover(db: Session, project_no: str, file: UploadFile, user_id: int | None) -> Project:
    """Records the client's hand-over acknowledgment -- the last
    client-facing confirmation in the workflow. Previously an email OTP
    the client read back to staff; now a scan of their physically
    signed acknowledgment, uploaded here as the confirmation record
    (see document_service.create_document, stored as a "Report"-typed
    project Document). There's no code to verify, so this is a direct
    manual action rather than a hard-gated one -- the signed upload is
    the evidence, not a cryptographic proof. Only reachable once
    notify_handover_ready has actually flagged the project ready
    (handover_sent_at set) AND payment has been confirmed
    (confirm_handover_payment); on success, flips project.status to
    'Completed' via the normal set_status path (same transition
    validation/audit logging every other status change gets)."""
    project = get_project(db, project_no)
    if project.handover_sent_at is None:
        raise ValidationAppError("This project isn't ready for hand-over yet.")
    if project.handover_payment_confirmed_at is None:
        raise ValidationAppError("Confirm payment received (Payment Confirmation tab) before completing hand-over.")
    assert_pdf_upload(file)

    document_service.create_document(
        db, project.project_no, f"Signed Hand-over Acknowledgment {project.project_no}", "Report", file, user_id,
    )

    project.handover_acknowledged_at = datetime.now(timezone.utc)
    db.commit()

    project = set_status(db, project_no, "Completed", None, user_id)
    recompute_progress(db, project)
    db.commit()
    db.refresh(project)
    return project


def check_and_notify_unpaid_completed_projects(db: Session) -> int:
    """Finds projects that have reached the Handover stage (every
    included Design/Permit/Supervision track already closed -- see
    _assert_stage_exit_criteria's Handover branch) but haven't had
    payment confirmed yet (confirm_handover_payment), and notifies every
    Administrator once per episode -- unpaid_completion_notified_at
    prevents re-notifying every run; cleared here the moment payment
    gets confirmed (nothing else clears it). Same "periodic check, plain
    callable function" shape as check_and_notify_stale_projects above."""
    candidates = (
        db.query(Project)
        .filter(Project.deleted_at.is_(None), Project.current_stage == "Handover", Project.status != "Completed")
        .all()
    )

    notified_count = 0
    for project in candidates:
        payment_confirmed = project.handover_payment_confirmed_at is not None

        if not payment_confirmed:
            if project.unpaid_completion_notified_at is None:
                notification_service.notify_role(
                    db, "Administrator",
                    "Project finished but not fully paid",
                    f"{project.project_name} ({project.project_no}) has every planned Design/Permit/"
                    "Supervision item closed, but is not yet fully paid.",
                    "Project",
                    link_route_name="project-workspace", link_params={"projectId": project.project_no},
                )
                project.unpaid_completion_notified_at = datetime.now(timezone.utc)
                notified_count += 1
        elif project.unpaid_completion_notified_at is not None:
            project.unpaid_completion_notified_at = None

    db.commit()
    return notified_count


def check_and_notify_overdue_projects(db: Session) -> int:
    """Finds Active projects past their target_date and notifies every
    Administrator once per episode -- overdue_notified_at prevents
    re-notifying every run; cleared if target_date is pushed back out
    (update_project) or the project stops being Active, the moment the
    condition that caused the alert stops being true. Same shape as
    check_and_notify_stale_projects above."""
    today = date.today()
    candidates = (
        db.query(Project)
        .filter(Project.deleted_at.is_(None), Project.status == "Active", Project.target_date < today)
        .all()
    )

    notified_count = 0
    for project in candidates:
        if project.overdue_notified_at is not None:
            continue
        notification_service.notify_role(
            db, "Administrator",
            "Project past its target date",
            f"{project.project_name} ({project.project_no}) was due on {project.target_date.isoformat()} "
            "and is still Active.",
            "Project",
            link_route_name="project-workspace", link_params={"projectId": project.project_no},
        )
        project.overdue_notified_at = datetime.now(timezone.utc)
        notified_count += 1

    db.commit()
    return notified_count
