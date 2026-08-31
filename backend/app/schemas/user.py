from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.permissions import ROLES
from app.models.user import User


def _avatar_initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


class UserOut(BaseModel):
    id: str
    name: str
    designation: str | None
    email: EmailStr
    mobile: str | None
    role: str
    avatar: str
    status: str

    @staticmethod
    def from_model(user: User) -> "UserOut":
        return UserOut(
            id=f"USR-{user.id:03d}",
            name=user.full_name,
            designation=user.designation,
            email=user.email,
            mobile=user.mobile,
            role=user.role,
            avatar=_avatar_initials(user.full_name),
            status="Active" if user.is_active else "Inactive",
        )


class UserCreatedOut(UserOut):
    temporary_password: str


class UserPasswordResetOut(UserOut):
    temporary_password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    designation: str | None = Field(default=None, max_length=120)
    mobile: str | None = Field(default=None, max_length=30)
    role: str

    @field_validator("role")
    @classmethod
    def role_must_be_known(cls, value: str) -> str:
        if value not in ROLES:
            raise ValueError(f"role must be one of {ROLES}")
        return value


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    designation: str | None = Field(default=None, max_length=120)
    mobile: str | None = Field(default=None, max_length=30)
    role: str | None = None

    @field_validator("role")
    @classmethod
    def role_must_be_known(cls, value: str | None) -> str | None:
        if value is not None and value not in ROLES:
            raise ValueError(f"role must be one of {ROLES}")
        return value


class UserStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def status_must_be_known(cls, value: str) -> str:
        if value not in ("Active", "Inactive"):
            raise ValueError("status must be 'Active' or 'Inactive'")
        return value


class RolePermissionOut(BaseModel):
    module: str
    view: bool
    edit: bool
    delete: bool


class RoleDefinitionOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    role: str
    description: str
    permissions: list[RolePermissionOut]


class RolePermissionIn(BaseModel):
    module: str
    view: bool
    edit: bool
    delete: bool


class RoleDefinitionUpdate(BaseModel):
    """Body for PATCH /api/roles/{role}. Always the full permission
    matrix for the role (all modules), same "whole set, not a diff"
    shape the frontend's PermissionMatrix edits in one save -- simpler
    to reason about than a partial per-cell PATCH."""

    permissions: list[RolePermissionIn]
