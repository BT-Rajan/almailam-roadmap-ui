from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.message import MESSAGE_CHANNELS


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class MessageTemplateOut(BaseModel):
    id: str
    name: str
    channel: str
    body: str

    @staticmethod
    def from_model(template) -> "MessageTemplateOut":
        return MessageTemplateOut(
            id=f"MTPL-{template.id:03d}", name=template.name, channel=template.channel, body=template.body
        )


class MessageTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    channel: str
    body: str = Field(min_length=1)
    _check = field_validator("channel")(_enum_validator(MESSAGE_CHANNELS, "channel"))


class MessageLogEntryOut(BaseModel):
    id: str
    clientId: str
    channel: str
    templateId: str | None
    body: str
    projectId: str | None
    status: str
    sentAt: datetime

    @staticmethod
    def from_model(entry, client_display_id: str, project_no: str | None) -> "MessageLogEntryOut":
        return MessageLogEntryOut(
            id=f"MSG-{entry.id:03d}",
            clientId=client_display_id,
            channel=entry.channel,
            templateId=f"MTPL-{entry.template_id:03d}" if entry.template_id else None,
            body=entry.body,
            projectId=project_no,
            status=entry.status,
            sentAt=entry.sent_at,
        )


class SendMessagePayload(BaseModel):
    clientId: str
    channel: str
    templateId: str | None = None
    body: str = Field(min_length=1)
    projectId: str | None = None
    _check = field_validator("channel")(_enum_validator(MESSAGE_CHANNELS, "channel"))
