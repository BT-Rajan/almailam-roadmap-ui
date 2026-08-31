from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    # Resolved against username OR employee_id OR customer_id (see
    # auth_service.login) -- 120 matches users.username, the widest of
    # the three since it's now the login email for most accounts
    # (migration 0058), not a short slug.
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def not_trivial(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must mix letters, numbers, or symbols.")
        return value
