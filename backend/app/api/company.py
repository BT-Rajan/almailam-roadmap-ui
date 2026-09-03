import mimetypes

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.file_storage import resolve_path
from app.models.user import User
from app.schemas.company import CompanySettingsIn, CompanySettingsOut
from app.services import company_service

router = APIRouter(prefix="/api/company", tags=["company"])

# Company settings are Administration-level configuration, same module the
# rest of the admin settings pages (users, roles, workflows) are gated
# behind.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/settings", response_model=CompanySettingsOut)
def get_settings(db: Session = Depends(get_db), _=Depends(can_view)):
    return CompanySettingsOut.from_model(company_service.get_settings(db))


@router.post("/settings", response_model=CompanySettingsOut)
def save_settings(
    payload: CompanySettingsIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    settings = company_service.save_settings(db, payload, current_user.id)
    return CompanySettingsOut.from_model(settings)


@router.post("/logo", response_model=CompanySettingsOut)
def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    settings = company_service.upload_logo(db, file, current_user.id)
    return CompanySettingsOut.from_model(settings)


@router.get("/logo")
def get_logo(db: Session = Depends(get_db), _=Depends(can_view)):
    settings = company_service.get_settings(db)
    if not settings.logo_storage_key:
        raise NotFoundError("Company logo")
    content_type = mimetypes.guess_type(settings.logo_original_filename or "")[0] or "application/octet-stream"
    return Response(content=resolve_path(settings.logo_storage_key).read_bytes(), media_type=content_type)


@router.delete("/logo", response_model=CompanySettingsOut)
def delete_logo(db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    settings = company_service.delete_logo(db, current_user.id)
    return CompanySettingsOut.from_model(settings)
