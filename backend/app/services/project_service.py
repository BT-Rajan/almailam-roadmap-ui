from datetime import datetime, timezone

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
from app.models.project import Project
from app.models.user import User
from app.services import audit_service, client_service, timeline_service, user_service
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
    )
    db.add(project)
    db.flush()
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
    if payload.progress is not None and payload.progress != project.progress:
        changes["progress"] = (project.progress, payload.progress)
        project.progress = payload.progress
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


def set_stage(db: Session, project_no: str, new_stage: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    previous_stage = project.current_stage
    assert_transition_allowed(
        PROJECT_STAGE_ALLOWED_TRANSITIONS, previous_stage, new_stage, "project"
    )
    if new_stage in PROJECT_STAGE_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_stage}'.")
    # Reopening a Completed project is exceptional and source-dependent
    # (unlike "Review" -> "Approval", the normal reason-free outcome of
    # a successful review), so this can't live in the target-state-only
    # REQUIRING_REASON table -- it's checked here instead.
    if previous_stage == "Completed" and new_stage == "Approval":
        assert_reason_given(reason, "A reason is required to reopen a completed project.")

    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Stage changed", user_id,
        previous_value=previous_stage, new_value=new_stage, reason=reason,
    )
    project.current_stage = new_stage
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

    db.commit()
    db.refresh(project)
    return project


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
    if new_status == "Completed" and project.progress != 100:
        # Otherwise a project could show "Completed" status next to a
        # progress bar reading e.g. 40% -- a visible, confusing
        # inconsistency between two fields that should agree once
        # something is actually done. Auto-correct rather than block the
        # transition on it, since making staff do a separate progress
        # update first just for this would be needless friction for
        # something this unambiguous.
        project.progress = 100
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
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project deleted", actor_id, previous_value=project.project_name)
    project.deleted_at = datetime.now(timezone.utc)
    db.commit()
