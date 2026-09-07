import mimetypes

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.file_storage import resolve_path
from app.models.user import User
from app.schemas.company import CompanyBrandingOut, CompanySettingsIn, CompanySettingsOut
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


@router.get("/branding", response_model=CompanyBrandingOut)
def get_branding(db: Session = Depends(get_db)):
    """Unlike /settings above, entirely public -- no auth at all, not
    even a bare login. The sign-in screen itself needs the brand color
    and logo before anyone has a session, and every logged-in role
    (Customer/Site portal included) needs them too to theme its own UI
    consistently with whatever an admin has configured. None of these
    three fields (company name, brand color, whether a logo exists) is
    sensitive. See CompanyBrandingOut's own docstring for why this is a
    separate, narrower endpoint rather than just loosening /settings."""
    return CompanyBrandingOut.from_model(company_service.get_settings(db))


@router.get("/branding/logo")
def get_public_logo(db: Session = Depends(get_db)):
    """The actual logo image, just as public as /branding above (and
    for the same reason -- the sign-in screen and every portal's own
    header need to render it via a plain <img src>, which can't send an
    Authorization header the way GET /logo below requires). Same
    lookup/response shape as /logo, just without the Administration:view
    gate."""
    settings = company_service.get_settings(db)
    if not settings.logo_storage_key:
        raise NotFoundError("Company logo")
    content_type = mimetypes.guess_type(settings.logo_original_filename or "")[0] or "application/octet-stream"
    return Response(content=resolve_path(settings.logo_storage_key).read_bytes(), media_type=content_type)


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
