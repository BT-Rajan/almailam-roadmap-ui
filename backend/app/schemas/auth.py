from pydantic import BaseModel, Field, field_validator

from app.schemas.company import CompanyBrandingOut
from app.schemas.server_time import ServerTimeOut
from app.schemas.user import CurrentUserOut


class LoginRequest(BaseModel):
    # Resolved against username OR employee_id (see auth_service.login)
    # -- 120 matches users.username, the wider of the two since it's
    # now the login email for most accounts (migration 0058), not a
    # short slug.
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=72)


class SessionBootstrapOut(BaseModel):
    """What every signed-in screen needs before it can show anything
    correctly, sent with each new token so starting the app isn't three
    more requests after sign-in (GET /api/server-time, /api/company/branding,
    /api/knowledge/status -- which all stay, same shapes, for callers that
    need them on their own)."""

    serverTime: ServerTimeOut
    branding: CompanyBrandingOut
    # Whether the knowledgebase assistant is on. False for a user without
    # Knowledgebase view access, who can't use it either way.
    knowledgeEnabled: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # The signed-in user (same shape as GET /api/auth/me), so starting or
    # resuming a session is one round trip instead of two.
    user: CurrentUserOut | None = None
    session: SessionBootstrapOut | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def not_trivial(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must mix letters, numbers, or symbols.")
        return value
