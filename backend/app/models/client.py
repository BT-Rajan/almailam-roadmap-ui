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
IDENTIFICATION_TYPES = ("Civil ID", "Passport", "Trade Licence", "Other")
CONSENT_TYPES = (
    "Process Personal Information",
    "Electronic Communication",
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
        default="Ready",
    )
    # Set by client_service.check_and_notify_stale_onboarding() once the
    # account manager has been notified that this client's onboarding
    # hasn't moved in a while -- mirrors Project.stale_notified_at.
    # Cleared the moment onboarding_state actually changes (see
    # set_onboarding_state), so a fresh staleness period starts if it
    # stalls again later at a different step.
    onboarding_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    # Staff member who owns this client relationship -- distinct from the
    # engineer assigned to any one of their projects. Nullable/unassigned
    # by default; set to NULL rather than blocked if that user is later
    # deactivated, so the client record itself is never held hostage by a
    # staffing change.
    account_manager_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Free-text internal notes (preferences, risk flags, handling
    # instructions) -- distinct from ClientVerification.notes, which is
    # scoped to one specific verification check.
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class ClientContact(Base, SoftDeleteMixin):
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


class ClientAddress(Base, SoftDeleteMixin):
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


class ClientIdentification(Base, SoftDeleteMixin):
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


CLIENT_DOCUMENT_CATEGORIES = (
    "Identity Document",
    "Passport",
    "Trade Licence",
    "Registration Document",
    "Authorisation Document",
    "Other",
)
CLIENT_VERIFICATION_RESULTS = ("Pending", "Verified", "Rejected")


class ClientDocument(Base, SoftDeleteMixin):
    __tablename__ = "client_documents"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        Enum(*CLIENT_DOCUMENT_CATEGORIES, name="client_document_category"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(150), nullable=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    verification_status: Mapped[str] = mapped_column(
        Enum(*CLIENT_VERIFICATION_RESULTS, name="client_verification_result"),
        nullable=False,
        default="Pending",
    )
    uploaded_by: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    upload_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # -- stored file (see app/core/file_storage.save_upload) --
    # storage_key is a generated name under UPLOADS_DIR, never the
    # client-supplied filename -- same pattern as app/models/document.py.
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)


class ClientDocumentVersion(Base):
    """Mirrors app/models/document.py's DocumentVersion for project
    documents -- client documents previously had none of this: replacing
    a file just bumped the version number and overwrote storage_key in
    place, with no history and no way to ever recover the file that was
    replaced (even though it was never actually deleted from disk)."""

    __tablename__ = "client_document_versions"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("client_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(nullable=False)
    uploaded_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)


class ClientVerification(Base):
    __tablename__ = "client_verifications"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        BigPK, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Optional link to the specific document this verification check was
    # performed against (e.g. verifying a Trade Licence upload). Null for
    # checklist-style verifications that aren't tied to one document (e.g.
    # confirming a registration number by phone).
    document_id: Mapped[int | None] = mapped_column(
        BigPK, ForeignKey("client_documents.id", ondelete="SET NULL"), nullable=True
    )
    item: Mapped[str] = mapped_column(String(150), nullable=False)
    result: Mapped[str] = mapped_column(
        Enum(*CLIENT_VERIFICATION_RESULTS, name="client_verification_result_2"), nullable=False
    )
    verified_by: Mapped[int] = mapped_column(
        BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    verified_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
