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
    """Columns for the entities that used to gate a step behind a
    client reading back a one-time email code -- Client, Project,
    Quotation, Contract, PendingClientOnboarding. That whole flow (see
    the removed app/core/otp.py) was replaced by staff uploading a scan
    of the client's physically signed copy instead (see
    quotation_service.confirm_quotation_approval and its siblings), so
    nothing writes these columns anymore; kept as inert columns rather
    than a destructive migration to drop them."""

    otp_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    otp_attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    otp_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
