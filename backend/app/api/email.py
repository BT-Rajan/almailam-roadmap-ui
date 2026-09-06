from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.email_settings import EmailSettingsIn, EmailSettingsOut, EmailSettingsTestResult
from app.services import email_settings_service

router = APIRouter(prefix="/api/email", tags=["email"])

# Email settings are Administration-level configuration, same module the
# rest of the admin settings pages (users, company, AI) are gated behind.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/providers")
def list_email_providers(_: User = Depends(can_view)):
    """Preset SMTP host/port values per provider, for the frontend's
    provider picker to fill the form with on selection -- see
    email_settings_service.PROVIDER_PRESETS."""
    return email_settings_service.PROVIDER_PRESETS


@router.get("/settings", response_model=EmailSettingsOut)
def get_email_settings(db: Session = Depends(get_db), _: User = Depends(can_view)):
    row = email_settings_service.get(db)
    return EmailSettingsOut.from_model(row, env_override_active=bool(get_settings().SMTP_HOST))


@router.post("/settings", response_model=EmailSettingsOut)
def update_email_settings(
    payload: EmailSettingsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    row = email_settings_service.update(
        db,
        {
            "provider": payload.provider,
            "smtp_host": payload.smtpHost,
            "smtp_port": payload.smtpPort,
            "smtp_use_tls": payload.smtpUseTls,
            "username": payload.username,
            "password": payload.password,
            "from_email": payload.fromEmail,
            "from_name": payload.fromName,
            "is_active": payload.isActive,
        },
        current_user.id,
    )
    return EmailSettingsOut.from_model(row, env_override_active=bool(get_settings().SMTP_HOST))


@router.post("/settings/test-connection", response_model=EmailSettingsTestResult)
def test_email_connection(db: Session = Depends(get_db), _: User = Depends(can_edit)):
    result = email_settings_service.test_connection(db)
    return EmailSettingsTestResult(ok=result["ok"], message=result["message"])
