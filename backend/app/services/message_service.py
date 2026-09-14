import mimetypes
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.models.message import MessageAttachment, MessageLogEntry, MessageTemplate
from app.models.project import Project
from app.services import client_service, email_service


def parse_template_id(raw: str) -> int:
    text = raw.removeprefix("MTPL-") if raw.upper().startswith("MTPL-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid template id.")
    return int(text)


def parse_attachment_id(raw: str) -> int:
    text = raw.removeprefix("MATT-") if raw.upper().startswith("MATT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid attachment id.")
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
    """SMS/WhatsApp only -- these two channels have no real integration
    yet, so this only ever simulates sending (status hardcoded to
    'Sent') and logs it. Email now sends for real (see send_email
    below), so routing it through here as well would silently mark an
    email 'Sent' without anything actually going out -- refused instead
    of quietly lying about it."""
    if payload.channel == "Email":
        raise ValidationAppError(
            "Email is sent through the compose-email action (with a subject and optional "
            "attachments), not this endpoint."
        )
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


def list_attachments(db: Session, message_log_id: int) -> list[MessageAttachment]:
    return (
        db.query(MessageAttachment)
        .filter(MessageAttachment.message_log_id == message_log_id)
        .order_by(MessageAttachment.id.asc())
        .all()
    )


def get_attachment(db: Session, attachment_id: int) -> MessageAttachment:
    attachment = db.query(MessageAttachment).filter(MessageAttachment.id == attachment_id).first()
    if attachment is None:
        raise NotFoundError("Attachment")
    return attachment


def send_email(
    db: Session,
    client_id: str,
    subject: str,
    body: str,
    project_id: str | None,
    files: list[UploadFile],
) -> MessageLogEntry:
    """The Message Centre's real send path (see send_message's own
    refusal above for why Email doesn't go through that one) -- clicking
    a customer opens a compose-email modal defaulting the subject to
    "{project name} - {current stage}" (see MessageCentrePage.vue), with
    optional file attachments, and this actually delivers it over SMTP
    via email_service rather than just logging a claimed send.

    Files are saved to disk up front (same storage as project
    documents, see file_storage.save_upload) before the send attempt --
    that way an attachment record survives even if the SMTP send itself
    fails, and the saved copy (not the request's already-consumed
    upload stream) is what gets read back and attached to the outgoing
    message.

    A send failure doesn't raise past this point -- it's recorded as a
    'Failed' MessageLogEntry (with the reason in error_message) exactly
    like a successful send is recorded as 'Sent', so it shows up the
    same way in the Message Centre's own history rather than just
    vanishing into a toast. The caller (see api/messages.py) still
    re-raises so the person composing the email sees an immediate error
    too.
    """
    client = client_service.get_client(db, client_service.parse_client_id(client_id))
    if not client.email:
        raise ValidationAppError("This customer has no email address on file.")

    if not subject.strip():
        raise ValidationAppError("Subject is required.")
    if not body.strip():
        raise ValidationAppError("Message body is required.")

    resolved_project_id = None
    if project_id:
        project = db.query(Project).filter(Project.project_no == project_id).first()
        if project is None:
            raise ValidationAppError("projectId does not refer to a known project.")
        resolved_project_id = project.id

    saved_attachments: list[tuple[str, str, int]] = [
        save_upload(f, "message-attachments") for f in files if f.filename
    ]

    status = "Sent"
    error_message: str | None = None
    try:
        attachments_for_email: list[tuple[bytes, str, str]] = []
        for storage_key, original_filename, _size in saved_attachments:
            content = resolve_path(storage_key).read_bytes()
            mimetype = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
            attachments_for_email.append((content, original_filename, mimetype))
        email_service.send_email_with_attachments(client.email, subject.strip(), body, attachments_for_email, db=db)
    except ValidationAppError as exc:
        status = "Failed"
        error_message = exc.message

    entry = MessageLogEntry(
        client_id=client.id,
        channel="Email",
        template_id=None,
        subject=subject.strip(),
        body=body,
        project_id=resolved_project_id,
        status=status,
        error_message=error_message,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()
    for storage_key, original_filename, size_bytes in saved_attachments:
        db.add(
            MessageAttachment(
                message_log_id=entry.id,
                storage_key=storage_key,
                original_filename=original_filename,
                file_size_bytes=size_bytes,
            )
        )
    db.commit()
    db.refresh(entry)

    if status == "Failed":
        raise ValidationAppError(error_message or "Failed to send email.")

    return entry
