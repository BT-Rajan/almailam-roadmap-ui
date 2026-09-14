from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
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
    # Email-only (migration 0098) -- SMS/WhatsApp have no subject line,
    # so this stays NULL for those channels. Defaults to
    # "{project name} - {current stage}" from the Message Centre
    # compose modal (see MessageCentrePage.vue), but stored as whatever
    # was actually typed/edited at send time, same as body.
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(Enum(*MESSAGE_STATUSES, name="message_status"), nullable=False)
    # Populated only when status == 'Failed' (migration 0098) -- an
    # Email send goes through real SMTP (see email_service.py) and can
    # genuinely fail (bad credentials, unreachable host, ...), unlike
    # the SMS/WhatsApp channels which only ever simulate sending and
    # so never produce a real error to record here.
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MessageAttachment(Base):
    """A file attached to an Email-channel MessageLogEntry (migration
    0098) -- SMS/WhatsApp entries never have any. Stored the same way
    as ProjectDocument (file_storage.save_upload's storage_key +
    original_filename + size), but deliberately its own table rather
    than reusing ProjectDocument: an emailed attachment isn't a project
    document (no version history, no stage/exit-criteria involvement,
    no requirement that a project even be selected), just a record of
    what was sent."""

    __tablename__ = "message_attachments"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    message_log_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("message_log.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
