from pydantic import BaseModel, Field


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
    brandColor: str = Field(default="#1D4ED8", max_length=20)
    defaultLanguage: str = Field(default="English")
    timezone: str = Field(default="Asia/Dubai", max_length=60)
    dateFormat: str = Field(default="DD/MM/YYYY", max_length=20)
    currency: str = Field(default="AED", max_length=10)
    defaultPaymentTermsDays: int = Field(default=30, ge=0, le=365)
    defaultQuotationValidityDays: int = Field(default=14, ge=0, le=365)
    staleProjectAlertDays: int = Field(default=45, ge=1, le=365)
