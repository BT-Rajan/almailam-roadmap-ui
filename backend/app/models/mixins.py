from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmailOtpMixin:
    """Columns for any entity that gates a step behind a client reading
    back a one-time email code -- see app/core/otp.py for the shared
    generation/hashing/expiry logic every user of this mixin calls.
    otp_code_hash is bcrypt-hashed the same way as User.password_hash,
    never stored in plaintext. All four are cleared the moment
    verification succeeds (or the content being confirmed changes, so a
    stale code can never be replayed against different content) -- a
    non-null otp_code_hash always means "a code is currently
    outstanding"."""

    otp_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    otp_attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    otp_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
