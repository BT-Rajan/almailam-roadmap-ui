from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EmailSettingsOut(BaseModel):
    provider: str
    smtpHost: str
    smtpPort: int
    smtpUseTls: bool
    username: str
    hasPassword: bool  # never the real/masked password itself
    fromEmail: str
    fromName: str
    isActive: bool
    lastTestedAt: datetime | None = None
    lastTestOk: bool | None = None
    lastTestError: str | None = None
    # True when SMTP_HOST is set in the server's .env -- that override
    # always wins over this saved row (see email_service._resolve_smtp_config),
    # so the admin form shows it as informational context rather than
    # letting an edit here look like it silently did nothing.
    envOverrideActive: bool

    @staticmethod
    def from_model(row, env_override_active: bool) -> "EmailSettingsOut":
        return EmailSettingsOut(
            provider=row.provider,
            smtpHost=row.smtp_host,
            smtpPort=row.smtp_port,
            smtpUseTls=row.smtp_use_tls,
            username=row.username,
            hasPassword=bool(row.password_encrypted),
            fromEmail=row.from_email,
            fromName=row.from_name,
            isActive=row.is_active,
            lastTestedAt=row.last_tested_at,
            lastTestOk=row.last_test_ok,
            lastTestError=row.last_test_error,
            envOverrideActive=env_override_active,
        )


class EmailSettingsIn(BaseModel):
    provider: str = Field(default="gmail", max_length=20)
    smtpHost: str = Field(default="", max_length=255)
    smtpPort: int = Field(default=587, ge=1, le=65535)
    smtpUseTls: bool = True
    username: str = Field(default="", max_length=255)
    # Omitted/None keeps the previously saved password (mirrors the
    # masked-apiKey convention in ai_config). Empty string explicitly
    # clears it.
    password: str | None = Field(default=None, max_length=255)
    fromEmail: str = Field(default="", max_length=255)
    fromName: str = Field(default="", max_length=255)
    isActive: bool = True

    @field_validator("smtpHost", "username", "fromEmail", "fromName", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        # Prone to being copy-pasted -- an app password or host copied
        # from somewhere that displays it with spacing, or a trailing
        # newline, would otherwise be saved verbatim and silently break
        # the connection with no validation error.
        return v.strip() if isinstance(v, str) else v


class EmailSettingsTestResult(BaseModel):
    ok: bool
    message: str
