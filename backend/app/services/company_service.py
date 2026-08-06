from sqlalchemy.orm import Session

from app.models.company import CompanySettings
from app.services import audit_service

ENTITY_TYPE = "COMPANY_SETTINGS"


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
    db.commit()
    db.refresh(settings)
    return settings
