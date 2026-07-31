from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.permissions import ROLES
from app.models.mixins import SoftDeleteMixin, TimestampMixin

# MySQL (production) gets a real BIGINT AUTO_INCREMENT; SQLite (local/dev
# smoke tests only) gets its native INTEGER PRIMARY KEY rowid-alias so
# autoincrement still works there.
BigPK = BigInteger().with_variant(Integer, "sqlite")


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Values are the exact display strings the frontend's UserRole type
    # uses (see core/permissions.ROLES) -- this removes a translation
    # layer between the DB, the JWT role claim, and the API response.
    role: Mapped[str] = mapped_column(
        Enum(*ROLES, name="user_role"), nullable=False, default="Viewer"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
