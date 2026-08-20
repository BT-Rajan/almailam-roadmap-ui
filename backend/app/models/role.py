from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK


class RoleDefinition(Base, TimestampMixin):
    """A user role and its description. Replaces what used to be the
    hardcoded ROLE_DESCRIPTIONS dict in core/permissions.py -- rows are
    seeded from that dict on first access (see role_service._ensure_seeded)
    so an admin can see and, via RolePermission, edit access without a
    code change. The set of role *names* stays fixed (see core.permissions
    .ROLES, still used for the users.role DB enum and request validation);
    only what each role can do is editable here."""

    __tablename__ = "role_definitions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role_definition",
        order_by="RolePermission.module",
        cascade="all, delete-orphan",
    )


class RolePermission(Base):
    """One module's view/edit/delete flags for a role -- the actual data
    behind the Administration > Users > Roles & Permissions matrix, and
    the source of truth read by role_service.has_permission() to gate
    every protected API route (see api/deps.require_permission)."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "module", name="uq_role_permissions_role_module"),)

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role_definitions.id"), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    role_definition: Mapped[RoleDefinition] = relationship(back_populates="permissions")
