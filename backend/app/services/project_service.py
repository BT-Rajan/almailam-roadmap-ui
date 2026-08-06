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
from app.services import audit_service, client_service, user_service
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
    engineer_id = user_service.parse_user_id(payload.engineerId)
    engineer = db.query(User).filter(User.id == engineer_id, User.deleted_at.is_(None)).first()
    if engineer is None:
        raise ValidationAppError("engineerId does not refer to a known user.")

    project_no = next_number(db, "PROJECT")
    project = Project(
        project_no=project_no,
        project_name=payload.projectName,
        client_id=client.id,
        service=payload.service,
        engineer_id=engineer.id,
        priority=payload.priority,
        start_date=payload.startDate,
        target_date=payload.targetDate,
    )
    db.add(project)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, project.id, "Project created", user_id)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_no: str, payload, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    changes: dict[str, tuple] = {}

    if payload.projectName is not None and payload.projectName != project.project_name:
        changes["project_name"] = (project.project_name, payload.projectName)
        project.project_name = payload.projectName
    if payload.service is not None and payload.service != project.service:
        changes["service"] = (project.service, payload.service)
        project.service = payload.service
    if payload.priority is not None and payload.priority != project.priority:
        changes["priority"] = (project.priority, payload.priority)
        project.priority = payload.priority
    if payload.targetDate is not None and payload.targetDate != project.target_date:
        changes["target_date"] = (project.target_date, payload.targetDate)
        project.target_date = payload.targetDate
    if payload.progress is not None and payload.progress != project.progress:
        changes["progress"] = (project.progress, payload.progress)
        project.progress = payload.progress
    if payload.engineerId is not None:
        new_engineer_id = user_service.parse_user_id(payload.engineerId)
        if new_engineer_id != project.engineer_id:
            engineer = db.query(User).filter(User.id == new_engineer_id).first()
            if engineer is None:
                raise ValidationAppError("engineerId does not refer to a known user.")
            changes["engineer_id"] = (project.engineer_id, new_engineer_id)
            project.engineer_id = new_engineer_id

    audit_service.log_field_changes(db, ENTITY_TYPE, project.id, changes, user_id)
    db.commit()
    db.refresh(project)
    return project


def set_stage(db: Session, project_no: str, new_stage: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    assert_transition_allowed(
        PROJECT_STAGE_ALLOWED_TRANSITIONS, project.current_stage, new_stage, "project"
    )
    if new_stage in PROJECT_STAGE_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_stage}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Stage changed", user_id,
        previous_value=project.current_stage, new_value=new_stage, reason=reason,
    )
    project.current_stage = new_stage
    db.commit()
    db.refresh(project)
    return project


def set_status(db: Session, project_no: str, new_status: str, reason: str | None, user_id: int | None) -> Project:
    project = get_project(db, project_no)
    assert_transition_allowed(
        PROJECT_STATUS_ALLOWED_TRANSITIONS, project.status, new_status, "project"
    )
    if new_status in PROJECT_STATUS_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move the project to '{new_status}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, project.id, "Status changed", user_id,
        previous_value=project.status, new_value=new_status, reason=reason,
    )
    project.status = new_status
    db.commit()
    db.refresh(project)
    return project


def get_audit_events(db: Session, project_no: str) -> list[dict]:
    project = get_project(db, project_no)
    return audit_service.get_history(db, ENTITY_TYPE, project.id)
