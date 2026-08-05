from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK

MESSAGE_CHANNELS = ("Email", "SMS", "WhatsApp")
MESSAGE_STATUSES = ("Sent", "Failed")


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel: Mapped[str] = mapped_column(Enum(*MESSAGE_CHANNELS, name="message_channel"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class MessageLogEntry(Base):
    __tablename__ = "message_log"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(Enum(*MESSAGE_CHANNELS, name="message_log_channel"), nullable=False)
    template_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(Enum(*MESSAGE_STATUSES, name="message_status"), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
