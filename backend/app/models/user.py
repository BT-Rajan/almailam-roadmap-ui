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
    # 120, matching email below (migration 0058) -- username mirrors the
    # login email for every user except the 'admin' bootstrap account
    # (see user_service.create_user), so it needs the same width.
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    # Alternate login identifier -- auth_service.login() resolves by
    # username OR employee_id, one shared mechanism for both frontends
    # (staff app, Site Engineer Portal) rather than a separate login
    # endpoint/token type per portal. Nullable since only Site Engineer
    # Portal users have one set; every other login path keeps using
    # username. Same password_hash serves both -- this is an additional
    # way to identify the same account, not a separate credential.
    employee_id: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Mr./Ms. for this user -- printed ahead of full_name wherever a
    # generated document names them (see document_template_service.
    # _user_name), e.g. a quotation/contract's "Prepared By". Optional:
    # left blank, the document simply prints the bare name, same as
    # before this column existed (see migration 0097).
    salutation: Mapped[str | None] = mapped_column(Enum("Mr.", "Ms.", name="user_salutation"), nullable=True)
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
