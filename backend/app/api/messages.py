from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.file_storage import resolve_path
from app.schemas.message import (
    MessageAttachmentOut,
    MessageLogEntryOut,
    MessageTemplateCreate,
    MessageTemplateOut,
    SendMessagePayload,
)
from app.services import client_service, message_service

router = APIRouter(prefix="/api/messages", tags=["messages"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")


def _message_log_out(db: Session, entry) -> MessageLogEntryOut:
    attachments = [MessageAttachmentOut.from_model(a) for a in message_service.list_attachments(db, entry.id)]
    return MessageLogEntryOut.from_model(
        entry,
        message_service.client_display_id(entry.client_id),
        message_service.project_no_for(db, entry.project_id),
        attachments,
    )


@router.get("/templates", response_model=list[MessageTemplateOut])
def list_templates(channel: str | None = None, db: Session = Depends(get_db), _=Depends(can_view)):
    return [MessageTemplateOut.from_model(t) for t in message_service.list_templates(db, channel)]


@router.post("/templates", response_model=MessageTemplateOut, status_code=201)
def create_template(payload: MessageTemplateCreate, db: Session = Depends(get_db), _=Depends(can_edit)):
    return MessageTemplateOut.from_model(message_service.create_template(db, payload))


@router.get("/log", response_model=list[MessageLogEntryOut])
def list_log(
    clientId: str | None = None,
    projectId: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    client_id = client_service.parse_client_id(clientId) if clientId else None
    entries = message_service.list_log(db, client_id, projectId)
    return [_message_log_out(db, e) for e in entries]


@router.post("/send", response_model=MessageLogEntryOut, status_code=201)
def send_message(payload: SendMessagePayload, db: Session = Depends(get_db), _=Depends(can_edit)):
    entry = message_service.send_message(db, payload)
    return _message_log_out(db, entry)


@router.post("/send-email", response_model=MessageLogEntryOut, status_code=201)
def send_email(
    clientId: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    projectId: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    _=Depends(can_edit),
):
    """The Message Centre's real email send -- multipart rather than
    SendMessagePayload's plain JSON because it accepts file
    attachments. See message_service.send_email for the actual SMTP
    send + logging behavior, including how a delivery failure is both
    logged and surfaced to the caller."""
    entry = message_service.send_email(db, clientId, subject, body, projectId, files)
    return _message_log_out(db, entry)


@router.get("/log/{message_no}/attachments/{attachment_no}/download")
def download_attachment(
    message_no: str,
    attachment_no: str,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    attachment_id = message_service.parse_attachment_id(attachment_no)
    attachment = message_service.get_attachment(db, attachment_id)
    return FileResponse(resolve_path(attachment.storage_key), filename=attachment.original_filename)
