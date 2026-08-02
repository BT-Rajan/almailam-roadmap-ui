from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin
from app.models.user import BigPK

CLIENT_TYPES = ("Individual", "Company", "Organisation", "Government Entity", "Other")
CLIENT_STATUSES = ("Active", "Inactive")
CLIENT_ONBOARDING_STATES = (
    "Information Required",
    "Documents Required",
    "Verification Required",
    "Under Review",
    "Ready",
    "Rejected",
    "Suspended",
)
CONTACT_TYPES = (
    "Primary Contact",
    "Billing Contact",
    "Legal Contact",
    "Authorised Representative",
    "Technical Contact",
    "Other",
)
ADDRESS_TYPES = ("Registered", "Operating", "Residential", "Mailing")
IDENTIFICATION_TYPES = ("Emirates ID", "Passport", "Trade Licence", "Other")
CONSENT_TYPES = (
    "Process Personal Information",
    "Electronic Communication",
    "Receive Notifications",
    "Process Documents",
)
PREFERRED_CHANNELS = ("Email", "WhatsApp", "SMS", "Phone")


class Client(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_type: Mapped[str] = mapped_column(Enum(*CLIENT_TYPES, name="client_type"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(120), nullable=False)
    mobile: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*CLIENT_STATUSES, name="client_status"), nullable=False, default="Active"
    )
    onboarding_state: Mapped[str] = mapped_column(
        Enum(*CLIENT_ONBOARDING_STATES, name="client_onboarding_state"),
        nullable=False,
        default="Information Required",
    )

    # -- individualProfile (only populated when client_type == 'Individual') --
    ind_full_legal_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    ind_preferred_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ind_nationality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ind_date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    ind_country_of_residence: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # -- organisationProfile (only populated when client_type != 'Individual') --
    org_legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    org_trade_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    org_organisation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    org_registration_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    org_trade_licence_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    org_tax_identification_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    org_country_of_registration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    org_date_of_incorporation: Mapped[date | None] = mapped_column(Date, nullable=True)
    org_website: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # -- communicationPreference (always populated) --
    preferred_language: Mapped[str] = mapped_column(String(40), nullable=False, default="English")
    preferred_channel: Mapped[str] = mapped_column(
        Enum(*PREFERRED_CHANNELS, name="client_preferred_channel"), nullable=False, default="Email"
    )
    email_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whatsapp_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sms_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ClientContact(Base):
    __tablename__ = "client_contacts"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_type: Mapped[str] = mapped_column(Enum(*CONTACT_TYPES, name="client_contact_type"), nullable=False)
    mobile: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    is_authorised_representative: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ClientAddress(Base):
    __tablename__ = "client_addresses"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(Enum(*ADDRESS_TYPES, name="client_address_type"), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    area: Mapped[str | None] = mapped_column(String(120), nullable=True)
    street: Mapped[str | None] = mapped_column(String(150), nullable=True)
    building: Mapped[str | None] = mapped_column(String(120), nullable=True)


class ClientIdentification(Base):
    __tablename__ = "client_identifications"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(
        Enum(*IDENTIFICATION_TYPES, name="client_identification_type"), nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(60), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    issuing_country: Mapped[str] = mapped_column(String(80), nullable=False)


class ClientConsent(Base):
    __tablename__ = "client_consents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_type: Mapped[str] = mapped_column(Enum(*CONSENT_TYPES, name="client_consent_type"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    method: Mapped[str] = mapped_column(String(150), nullable=False)
    recorded_by: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
