from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.user import BigPK


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Set once at issuance (see auth_service._issue_tokens) and never
    # updated afterwards -- this token is single-use (rotated on refresh),
    # so "last used" for inactivity purposes just means "when was this
    # particular token minted", checked against now the moment it's
    # redeemed. See auth_service.refresh().
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
