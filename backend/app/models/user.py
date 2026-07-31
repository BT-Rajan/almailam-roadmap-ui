from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

# MySQL (production) gets a real BIGINT AUTO_INCREMENT; SQLite (local/dev
# smoke tests only) gets its native INTEGER PRIMARY KEY rowid-alias so
# autoincrement still works there.
BigPK = BigInteger().with_variant(Integer, "sqlite")

USER_ROLES = ("admin", "manager", "staff", "viewer")
USER_DEPARTMENTS = ("operations", "finance", "submissions", "management")


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    role: Mapped[str] = mapped_column(
        Enum(*USER_ROLES, name="user_role"), nullable=False, default="staff"
    )
    # NULL means no department scoping, i.e. read-only access outside what
    # role alone grants -- admin/manager bypass this regardless of value.
    department: Mapped[str | None] = mapped_column(
        Enum(*USER_DEPARTMENTS, name="user_department"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
