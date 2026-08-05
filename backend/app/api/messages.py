from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.message import (
    MessageLogEntryOut,
    MessageTemplateCreate,
    MessageTemplateOut,
    SendMessagePayload,
)
from app.services import client_service, message_service

router = APIRouter(prefix="/api/messages", tags=["messages"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")


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
    return [
        MessageLogEntryOut.from_model(
            e, message_service.client_display_id(e.client_id), message_service.project_no_for(db, e.project_id)
        )
        for e in entries
    ]


@router.post("/send", response_model=MessageLogEntryOut, status_code=201)
def send_message(payload: SendMessagePayload, db: Session = Depends(get_db), _=Depends(can_edit)):
    entry = message_service.send_message(db, payload)
    return MessageLogEntryOut.from_model(
        entry,
        message_service.client_display_id(entry.client_id),
        message_service.project_no_for(db, entry.project_id),
    )
