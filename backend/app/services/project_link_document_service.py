from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.document import ProjectLinkDocument
from app.models.project import Project
from app.models.user import User
from app.services import audit_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "PROJECT_LINK_DOCUMENT"


def user_name(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "System"
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _project_by_no(db: Session, project_no: str) -> Project:
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError("projectId does not refer to a known project.")
    return project


def list_for_project(db: Session, project_no: str, category: str | None = None) -> list[ProjectLinkDocument]:
    project = _project_by_no(db, project_no)
    query = db.query(ProjectLinkDocument).filter(
        ProjectLinkDocument.project_id == project.id,
        ProjectLinkDocument.deleted_at.is_(None),
    )
    if category:
        query = query.filter(ProjectLinkDocument.category == category)
    return query.order_by(ProjectLinkDocument.id.desc()).all()


def get_link_document(db: Session, link_document_no: str) -> ProjectLinkDocument:
    document = (
        db.query(ProjectLinkDocument)
        .filter(ProjectLinkDocument.link_document_no == link_document_no, ProjectLinkDocument.deleted_at.is_(None))
        .first()
    )
    if document is None:
        raise NotFoundError("Document")
    return document


def add_link_document(db: Session, project_no: str, payload, user_id: int) -> ProjectLinkDocument:
    project = _project_by_no(db, project_no)

    document = ProjectLinkDocument(
        link_document_no=next_number(db, "PROJECT_LINK_DOCUMENT"),
        project_id=project.id,
        category=payload.category,
        name=payload.name.strip(),
        path=payload.path.strip(),
        added_by=user_id,
        added_date=date.today(),
    )
    db.add(document)
    db.flush()

    audit_service.log_event(db, ENTITY_TYPE, document.id, "Document link added", user_id, new_value=document.name)
    timeline_service.create_system_event(
        db, project.id, "document",
        title=f"{payload.category} document added: {document.name}",
        actor_id=user_id,
    )
    db.commit()
    db.refresh(document)
    return document


def delete_link_document(db: Session, link_document_no: str, actor_id: int) -> None:
    document = get_link_document(db, link_document_no)
    audit_service.log_event(
        db, ENTITY_TYPE, document.id, "Document link removed", actor_id, previous_value=document.name
    )
    document.deleted_at = datetime.now(timezone.utc)
    db.commit()
