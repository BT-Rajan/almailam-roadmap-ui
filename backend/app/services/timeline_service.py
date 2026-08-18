from datetime import date

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


def _project_exists(db: Session, project_no: str) -> Project:
    """Like _get_project() but doesn't exclude soft-deleted projects --
    used only for the read-only list view, so a deleted project's own
    timeline stays inspectable the same way its audit trail does."""
    project = db.query(Project).filter(Project.project_no == project_no).first()
    if not project:
        raise NotFoundError("Project")
    return project


def list_for_project(db: Session, project_no: str) -> list[ProjectTimelineEvent]:
    project = _project_exists(db, project_no)
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


def create_system_event(
    db: Session, project_id: int, event_type: str, title: str, description: str | None = None,
    actor_id: int | None = None,
) -> ProjectTimelineEvent:
    """For automatic, system-generated timeline entries (currently just
    stage changes -- see project_service.set_stage). Does not commit;
    the caller is expected to be inside its own transaction already
    doing other work (updating the project, writing an audit event)."""
    event = ProjectTimelineEvent(
        project_id=project_id,
        type=event_type,
        title=title,
        description=description,
        event_date=date.today(),
        status="completed",
        created_by=actor_id,
    )
    db.add(event)
    return event


def get_last_stage_event(db: Session, project_id: int) -> ProjectTimelineEvent | None:
    """Used by project_service.check_and_notify_stale_projects() to
    determine how long a project has sat on its current stage -- kept
    here rather than having project_service query ProjectTimelineEvent
    directly, consistent with this module already owning all timeline-
    event queries."""
    return (
        db.query(ProjectTimelineEvent)
        .filter(ProjectTimelineEvent.project_id == project_id, ProjectTimelineEvent.type == "stage")
        .order_by(ProjectTimelineEvent.created_at.desc())
        .first()
    )


def create_event(db: Session, project_no: str, payload, actor_id: int) -> ProjectTimelineEvent:
    project = _get_project(db, project_no)
    if payload.status not in TIMELINE_EVENT_STATUSES:
        raise ValidationAppError(f"status must be one of {TIMELINE_EVENT_STATUSES}")
    event = ProjectTimelineEvent(
        project_id=project.id,
        # The dialog this comes from asks for a title, a date, and an
        # Upcoming/In Progress/Completed status -- that's milestone
        # vocabulary, not a general note, and it's the only entry point
        # that lets staff add anything the customer portal's Milestones
        # panel actually reads (which filters on type in
        # ('milestone', 'stage')). Previously hardcoded to "note", which
        # meant nothing created here could ever show up as a milestone
        # anywhere, despite the UI clearly being built for exactly that.
        type="milestone",
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
