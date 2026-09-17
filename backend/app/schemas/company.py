import re

from pydantic import BaseModel, Field, field_validator


class CompanySettingsOut(BaseModel):
    companyName: str
    tagline: str
    tradeLicenseNumber: str
    email: str
    phone: str
    website: str
    address: str
    city: str
    country: str
    brandColor: str
    defaultLanguage: str
    timezone: str
    dateFormat: str
    currency: str
    defaultPaymentTermsDays: int
    defaultQuotationValidityDays: int
    staleProjectAlertDays: int
    staleOnboardingAlertDays: int
    statusReportRecipientId: str | None = None
    hasLogo: bool = False
    logoFilename: str | None = None

    @staticmethod
    def from_model(settings) -> "CompanySettingsOut":
        return CompanySettingsOut(
            companyName=settings.company_name,
            tagline=settings.tagline,
            tradeLicenseNumber=settings.trade_license_number,
            email=settings.email,
            phone=settings.phone,
            website=settings.website,
            address=settings.address,
            city=settings.city,
            country=settings.country,
            brandColor=settings.brand_color,
            defaultLanguage=settings.default_language,
            timezone=settings.timezone,
            dateFormat=settings.date_format,
            currency=settings.currency,
            defaultPaymentTermsDays=settings.default_payment_terms_days,
            defaultQuotationValidityDays=settings.default_quotation_validity_days,
            staleProjectAlertDays=settings.stale_project_alert_days,
            staleOnboardingAlertDays=settings.stale_onboarding_alert_days,
            statusReportRecipientId=f"USR-{settings.status_report_recipient_id:03d}" if settings.status_report_recipient_id else None,
            hasLogo=bool(settings.logo_storage_key),
            logoFilename=settings.logo_original_filename,
        )


class CompanyBrandingOut(BaseModel):
    """The subset of CompanySettings every logged-in role (Site portal
    included, not just staff with Administration:view) needs to
    theme its own UI consistently -- see GET /api/company/branding.
    Deliberately excludes every other field on CompanySettingsOut (trade
    license, address, alert thresholds, etc.), which stay behind the
    Administration permission gate."""

    companyName: str
    brandColor: str
    hasLogo: bool = False

    @staticmethod
    def from_model(settings) -> "CompanyBrandingOut":
        return CompanyBrandingOut(
            companyName=settings.company_name,
            brandColor=settings.brand_color,
            hasLogo=bool(settings.logo_storage_key),
        )


class CompanySettingsIn(BaseModel):
    companyName: str = Field(min_length=1, max_length=150)
    tagline: str = Field(default="", max_length=200)
    tradeLicenseNumber: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=150)
    phone: str = Field(default="", max_length=30)
    website: str = Field(default="", max_length=150)
    address: str = Field(default="", max_length=250)
    city: str = Field(default="", max_length=80)
    country: str = Field(default="", max_length=80)
    brandColor: str = Field(default="#3995BE", max_length=20)
    defaultLanguage: str = Field(default="English")
    timezone: str = Field(default="Asia/Dubai", max_length=60)
    dateFormat: str = Field(default="DD/MM/YYYY", max_length=20)
    currency: str = Field(default="AED", max_length=10)
    defaultPaymentTermsDays: int = Field(default=30, ge=0, le=365)
    defaultQuotationValidityDays: int = Field(default=14, ge=0, le=365)
    staleProjectAlertDays: int = Field(default=45, ge=1, le=365)
    staleOnboardingAlertDays: int = Field(default=5, ge=1, le=365)
    statusReportRecipientId: str | None = None

    # Free text otherwise -- this value gets interpolated straight into
    # a <style> block in scheduled_report_pdf.py's PDF template (and
    # nowhere HTML-escaped there, since it's meant to be a CSS color
    # token, not text content), so a value like "red}</style><b>" would
    # break out of the CSS rule and inject arbitrary markup into an
    # emailed PDF. The frontend's own color-scale generator
    # (colorScale.ts's hexToRgb) already only ever accepts this same
    # #rgb/#rrggbb shape; this enforces that at the point data is saved,
    # not just where one particular consumer happens to read it.
    @field_validator("brandColor")
    @classmethod
    def _validate_brand_color(cls, v: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}", v):
            raise ValueError("brandColor must be a hex color like #3995BE.")
        return v
