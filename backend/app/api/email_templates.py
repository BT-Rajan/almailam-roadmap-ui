from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.email_template import EmailMergeField, EmailTemplateOut, EmailTemplateUpdate
from app.services import email_template_service

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])

# Same admin surface as SMTP settings (api/email.py) -- this is the
# Templates tab of the same Administration > Email Settings page.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, template) -> EmailTemplateOut:
    return EmailTemplateOut.from_model(template, _user_name(db, template.updated_by))


@router.get("", response_model=list[EmailTemplateOut])
def list_templates(db: Session = Depends(get_db), _=Depends(can_view)):
    return [_to_out(db, t) for t in email_template_service.list_templates(db)]


@router.get("/{key}", response_model=EmailTemplateOut)
def get_template(key: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, email_template_service.get_template(db, key))


@router.get("/{key}/merge-fields", response_model=list[EmailMergeField])
def list_merge_fields(key: str, _=Depends(can_view)):
    return email_template_service.get_merge_fields(key)


@router.patch("/{key}", response_model=EmailTemplateOut)
def update_template(
    key: str, payload: EmailTemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    template = email_template_service.update_template(db, key, payload.subject, payload.body, current_user.id)
    return _to_out(db, template)
