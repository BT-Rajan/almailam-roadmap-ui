from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.message import MessageLogEntry, MessageTemplate
from app.models.project import Project
from app.services import client_service


def parse_template_id(raw: str) -> int:
    text = raw.removeprefix("MTPL-") if raw.upper().startswith("MTPL-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid template id.")
    return int(text)


def parse_message_id(raw: str) -> int:
    text = raw.removeprefix("MSG-") if raw.upper().startswith("MSG-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid message id.")
    return int(text)


def list_templates(db: Session, channel: str | None = None) -> list[MessageTemplate]:
    query = db.query(MessageTemplate)
    if channel:
        query = query.filter(MessageTemplate.channel == channel)
    return query.order_by(MessageTemplate.id.asc()).all()


def get_template(db: Session, template_id: int) -> MessageTemplate:
    template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if template is None:
        raise NotFoundError("Message template")
    return template


def create_template(db: Session, payload) -> MessageTemplate:
    template = MessageTemplate(name=payload.name, channel=payload.channel, body=payload.body)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def list_log(db: Session, client_id: int | None = None, project_no: str | None = None) -> list[MessageLogEntry]:
    query = db.query(MessageLogEntry)
    if client_id is not None:
        query = query.filter(MessageLogEntry.client_id == client_id)
    if project_no:
        project = db.query(Project).filter(Project.project_no == project_no).first()
        query = query.filter(MessageLogEntry.project_id == (project.id if project else -1))
    return query.order_by(MessageLogEntry.sent_at.desc()).all()


def send_message(db: Session, payload) -> MessageLogEntry:
    client = client_service.get_client(db, client_service.parse_client_id(payload.clientId))

    template_id = None
    if payload.templateId:
        template = get_template(db, parse_template_id(payload.templateId))
        if template.channel != payload.channel:
            raise ValidationAppError("templateId does not match the given channel.")
        template_id = template.id

    project_id = None
    if payload.projectId:
        project = db.query(Project).filter(Project.project_no == payload.projectId).first()
        if project is None:
            raise ValidationAppError("projectId does not refer to a known project.")
        project_id = project.id

    entry = MessageLogEntry(
        client_id=client.id,
        channel=payload.channel,
        template_id=template_id,
        body=payload.body,
        project_id=project_id,
        status="Sent",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def client_display_id(client_id: int) -> str:
    return f"CLT-{client_id:03d}"


def project_no_for(db: Session, project_id: int | None) -> str | None:
    if project_id is None:
        return None
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.project_no if project else None
