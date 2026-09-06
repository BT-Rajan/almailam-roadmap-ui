from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class EmailSettings(Base, TimestampMixin):
    """Administration-level SMTP configuration used to send Quotation/
    Contract documents (see app.services.email_service). Single-row
    settings table, same pattern as CompanySettings/AIConfiguration --
    id is always 1.

    `password_encrypted` is Fernet-encrypted at rest (see
    app.core.security.encrypt_secret/decrypt_secret) -- never read or
    returned as plaintext outside email_settings_service. The
    SMTP_* environment variables in core/config.py remain a fallback
    that takes priority over this row when set, for deployments that
    would rather fix mail credentials at the infra level (see
    email_service._resolve_smtp_config).
    """

    __tablename__ = "email_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="gmail")
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False, default="smtp.gmail.com")
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_test_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_test_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
