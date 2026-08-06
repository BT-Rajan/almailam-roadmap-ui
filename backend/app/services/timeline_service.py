from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.project import Project
from app.models.timeline import TIMELINE_EVENT_STATUSES, ProjectTimelineEvent
from app.models.user import User

ENTITY_TYPE = "PROJECT_TIMELINE_EVENT"


def _get_project(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if not project:
        raise NotFoundError("Project")
    return project


def list_for_project(db: Session, project_no: str) -> list[ProjectTimelineEvent]:
    project = _get_project(db, project_no)
    return (
        db.query(ProjectTimelineEvent)
        .filter(ProjectTimelineEvent.project_id == project.id)
        .order_by(ProjectTimelineEvent.event_date.asc(), ProjectTimelineEvent.id.asc())
        .all()
    )


def user_name(db: Session, user_id: int | None) -> str | None:
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def create_event(db: Session, project_no: str, payload, actor_id: int) -> ProjectTimelineEvent:
    project = _get_project(db, project_no)
    if payload.status not in TIMELINE_EVENT_STATUSES:
        raise ValidationAppError(f"status must be one of {TIMELINE_EVENT_STATUSES}")
    event = ProjectTimelineEvent(
        project_id=project.id,
        # Every user-created entry from the timeline dialog is a free-form
        # note; the other event types (stage, document, quotation,
        # submission, milestone, task) are reserved for system-generated
        # entries from their respective workflows, which don't exist yet.
        type="note",
        title=payload.title,
        description=payload.description,
        event_date=payload.date,
        status=payload.status,
        created_by=actor_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, project_no: str, raw_id: str, payload) -> ProjectTimelineEvent:
    project = _get_project(db, project_no)
    text = raw_id.removeprefix("TLE-") if raw_id.upper().startswith("TLE-") else raw_id
    if not text.isdigit():
        raise ValidationAppError("Invalid timeline event id.")
    event = (
        db.query(ProjectTimelineEvent)
        .filter(ProjectTimelineEvent.id == int(text), ProjectTimelineEvent.project_id == project.id)
        .first()
    )
    if not event:
        raise NotFoundError("Timeline event")
    if payload.status is not None and payload.status not in TIMELINE_EVENT_STATUSES:
        raise ValidationAppError(f"status must be one of {TIMELINE_EVENT_STATUSES}")
    if payload.title is not None:
        event.title = payload.title
    if payload.description is not None:
        event.description = payload.description
    if payload.date is not None:
        event.event_date = payload.date
    if payload.status is not None:
        event.status = payload.status
    db.commit()
    db.refresh(event)
    return event
