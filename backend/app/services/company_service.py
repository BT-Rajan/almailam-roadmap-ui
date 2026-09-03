from sqlalchemy.orm import Session

from app.core.exceptions import ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.models.company import CompanySettings
from app.services import audit_service, user_service

ENTITY_TYPE = "COMPANY_SETTINGS"
LOGO_STORAGE_SUBDIRECTORY = "company-logo"
# PNG/JPEG only -- not SVG: InlineImage's underlying python-docx
# add_picture() rasterizes via Pillow, which can't read SVG, so an SVG
# upload would silently fail (or embed a broken image) the first time
# any template's {{ logo }} field actually renders.
_LOGO_EXTENSIONS = (".png", ".jpg", ".jpeg")


def get_settings(db: Session) -> CompanySettings:
    settings = db.query(CompanySettings).filter(CompanySettings.id == 1).first()
    if settings is None:
        # First run: create the single settings row with the model's
        # defaults so the admin page always has something sensible to show
        # and edit, rather than a permanent empty state.
        settings = CompanySettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def save_settings(db: Session, payload, actor_id: int) -> CompanySettings:
    settings = get_settings(db)
    audit_service.log_event(
        db, ENTITY_TYPE, settings.id, "Company settings updated", actor_id,
        previous_value=settings.company_name, new_value=payload.companyName,
    )
    settings.company_name = payload.companyName
    settings.tagline = payload.tagline
    settings.trade_license_number = payload.tradeLicenseNumber
    settings.email = payload.email
    settings.phone = payload.phone
    settings.website = payload.website
    settings.address = payload.address
    settings.city = payload.city
    settings.country = payload.country
    settings.brand_color = payload.brandColor
    settings.default_language = payload.defaultLanguage
    settings.timezone = payload.timezone
    settings.date_format = payload.dateFormat
    settings.currency = payload.currency
    settings.default_payment_terms_days = payload.defaultPaymentTermsDays
    settings.default_quotation_validity_days = payload.defaultQuotationValidityDays
    settings.stale_project_alert_days = payload.staleProjectAlertDays
    settings.stale_onboarding_alert_days = payload.staleOnboardingAlertDays
    settings.status_report_recipient_id = (
        user_service.parse_user_id(payload.statusReportRecipientId) if payload.statusReportRecipientId else None
    )
    db.commit()
    db.refresh(settings)
    return settings


def upload_logo(db: Session, file, actor_id: int) -> CompanySettings:
    """Replaces the single company-wide logo -- shared by every document
    template's {{ logo }} merge field (see document_template_service.
    _render_docx/_get_company_logo_path), not uploaded per-template."""
    if not (file.filename or "").lower().endswith(_LOGO_EXTENSIONS):
        raise ValidationAppError(f"Logo must be one of: {', '.join(_LOGO_EXTENSIONS)}.")

    settings = get_settings(db)
    previous_key = settings.logo_storage_key
    storage_key, original_filename, _size_bytes = save_upload(file, LOGO_STORAGE_SUBDIRECTORY)
    settings.logo_storage_key = storage_key
    settings.logo_original_filename = original_filename
    audit_service.log_event(db, ENTITY_TYPE, settings.id, "Company logo updated", actor_id, new_value=original_filename)
    db.commit()
    db.refresh(settings)

    if previous_key:
        resolve_path(previous_key).unlink(missing_ok=True)
    return settings


def delete_logo(db: Session, actor_id: int) -> CompanySettings:
    settings = get_settings(db)
    if not settings.logo_storage_key:
        return settings
    previous_key = settings.logo_storage_key
    audit_service.log_event(
        db, ENTITY_TYPE, settings.id, "Company logo removed", actor_id,
        previous_value=settings.logo_original_filename,
    )
    settings.logo_storage_key = None
    settings.logo_original_filename = None
    db.commit()
    db.refresh(settings)
    resolve_path(previous_key).unlink(missing_ok=True)
    return settings
