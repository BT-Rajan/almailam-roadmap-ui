from datetime import date, datetime

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.client import (
    ADDRESS_TYPES,
    CLIENT_DOCUMENT_CATEGORIES,
    CLIENT_ONBOARDING_STATES,
    CLIENT_STATUSES,
    CLIENT_TYPES,
    CLIENT_VERIFICATION_RESULTS,
    CONSENT_TYPES,
    CONTACT_TYPES,
    IDENTIFICATION_TYPES,
    PREFERRED_CHANNELS,
)


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


# Digits, spaces, +, -, (, ) only, with at least 7 actual digits -- matches
# the shape of validators.phone() on the frontend so both sides agree on
# what counts as a real phone number rather than just "non-empty".
_PHONE_PATTERN = re.compile(r"^[\d\s\-\+\(\)]+$")


def _phone_validator(label: str):
    def _check(value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if not _PHONE_PATTERN.match(value) or len(digits) < 7:
            raise ValueError(f"{label} must be a valid phone number (at least 7 digits)")
        return value

    return _check


# Permissive domain/URL matcher: accepts "example.com", "www.example.com",
# or a full "https://example.com/path" -- website fields in this app are
# typed in freely rather than copy-pasted, so a strict http(s):// prefix
# requirement would reject perfectly valid input.
_WEBSITE_PATTERN = re.compile(r"^(https?://)?([\w-]+\.)+[a-zA-Z]{2,}(/\S*)?$")


def _website_validator(label: str):
    def _check(value: str) -> str:
        if not _WEBSITE_PATTERN.match(value):
            raise ValueError(f"{label} must be a valid website address")
        return value

    return _check


def _not_future_validator(label: str):
    def _check(value: date) -> date:
        if value > date.today():
            raise ValueError(f"{label} cannot be in the future")
        return value

    return _check


# --- nested profile schemas -------------------------------------------------


class IndividualProfileIn(BaseModel):
    fullLegalName: str = Field(min_length=1, max_length=150)
    preferredName: str | None = Field(default=None, max_length=100)
    nationality: str = Field(min_length=1, max_length=80)
    dateOfBirth: date
    countryOfResidence: str = Field(min_length=1, max_length=80)

    _check_dob = field_validator("dateOfBirth")(_not_future_validator("dateOfBirth"))


class IndividualProfileOut(BaseModel):
    fullLegalName: str
    preferredName: str | None
    nationality: str
    dateOfBirth: date
    countryOfResidence: str


class OrganisationProfileIn(BaseModel):
    legalName: str = Field(min_length=1, max_length=200)
    tradeName: str | None = Field(default=None, max_length=200)
    organisationType: str = Field(min_length=1, max_length=100)
    registrationNumber: str = Field(min_length=1, max_length=60)
    tradeLicenceNumber: str | None = Field(default=None, max_length=60)
    taxIdentificationNumber: str | None = Field(default=None, max_length=60)
    countryOfRegistration: str = Field(min_length=1, max_length=80)
    dateOfIncorporation: date
    website: str | None = Field(default=None, max_length=200)

    _check_incorporation = field_validator("dateOfIncorporation")(_not_future_validator("dateOfIncorporation"))

    @field_validator("website")
    @classmethod
    def check_website(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return _website_validator("website")(value)


class OrganisationProfileOut(BaseModel):
    legalName: str
    tradeName: str | None
    organisationType: str
    registrationNumber: str
    tradeLicenceNumber: str | None
    taxIdentificationNumber: str | None
    countryOfRegistration: str
    dateOfIncorporation: date
    website: str | None


class CommunicationPreference(BaseModel):
    preferredLanguage: str = Field(default="English", max_length=40)
    preferredChannel: str = "Email"
    emailConsent: bool = False
    whatsappConsent: bool = False
    smsConsent: bool = False

    _check_channel = field_validator("preferredChannel")(
        _enum_validator(PREFERRED_CHANNELS, "preferredChannel")
    )


# --- client ------------------------------------------------------------------


class ClientOut(BaseModel):
    id: str
    code: str
    clientType: str
    companyName: str
    contactPerson: str
    mobile: str
    email: EmailStr
    city: str
    status: str
    onboardingState: str
    createdDate: date
    individualProfile: IndividualProfileOut | None = None
    organisationProfile: OrganisationProfileOut | None = None
    communicationPreference: CommunicationPreference

    @staticmethod
    def from_model(client) -> "ClientOut":
        code = f"CLT-{client.id:03d}"
        individual = None
        if client.client_type == "Individual":
            individual = IndividualProfileOut(
                fullLegalName=client.ind_full_legal_name,
                preferredName=client.ind_preferred_name,
                nationality=client.ind_nationality,
                dateOfBirth=client.ind_date_of_birth,
                countryOfResidence=client.ind_country_of_residence,
            )
        organisation = None
        if client.client_type != "Individual":
            organisation = OrganisationProfileOut(
                legalName=client.org_legal_name,
                tradeName=client.org_trade_name,
                organisationType=client.org_organisation_type,
                registrationNumber=client.org_registration_number,
                tradeLicenceNumber=client.org_trade_licence_number,
                taxIdentificationNumber=client.org_tax_identification_number,
                countryOfRegistration=client.org_country_of_registration,
                dateOfIncorporation=client.org_date_of_incorporation,
                website=client.org_website,
            )
        return ClientOut(
            id=code,
            code=code,
            clientType=client.client_type,
            companyName=client.company_name,
            contactPerson=client.contact_person,
            mobile=client.mobile,
            email=client.email,
            city=client.city,
            status=client.status,
            onboardingState=client.onboarding_state,
            createdDate=client.created_at.date(),
            individualProfile=individual,
            organisationProfile=organisation,
            communicationPreference=CommunicationPreference(
                preferredLanguage=client.preferred_language,
                preferredChannel=client.preferred_channel,
                emailConsent=client.email_consent,
                whatsappConsent=client.whatsapp_consent,
                smsConsent=client.sms_consent,
            ),
        )


class ClientCreate(BaseModel):
    clientType: str
    companyName: str = Field(min_length=1, max_length=200)
    contactPerson: str = Field(min_length=1, max_length=120)
    mobile: str = Field(min_length=1, max_length=30)
    email: EmailStr
    city: str = Field(min_length=1, max_length=80)
    individualProfile: IndividualProfileIn | None = Field(default=None, validate_default=True)
    organisationProfile: OrganisationProfileIn | None = Field(default=None, validate_default=True)
    communicationPreference: CommunicationPreference = CommunicationPreference()

    _check_type = field_validator("clientType")(_enum_validator(CLIENT_TYPES, "clientType"))
    _check_mobile = field_validator("mobile")(_phone_validator("mobile"))

    @field_validator("organisationProfile")
    @classmethod
    def profile_matches_type(cls, value, info):
        client_type = info.data.get("clientType")
        if client_type == "Individual" and value is not None:
            raise ValueError("organisationProfile must not be set when clientType is Individual")
        if client_type is not None and client_type != "Individual" and value is None:
            raise ValueError("organisationProfile is required unless clientType is Individual")
        return value

    @field_validator("individualProfile")
    @classmethod
    def individual_profile_matches_type(cls, value, info):
        client_type = info.data.get("clientType")
        if client_type == "Individual" and value is None:
            raise ValueError("individualProfile is required when clientType is Individual")
        if client_type != "Individual" and value is not None:
            raise ValueError("individualProfile must not be set unless clientType is Individual")
        return value


class ClientUpdate(BaseModel):
    companyName: str | None = Field(default=None, min_length=1, max_length=200)
    contactPerson: str | None = Field(default=None, min_length=1, max_length=120)
    mobile: str | None = Field(default=None, min_length=1, max_length=30)
    email: EmailStr | None = None
    city: str | None = Field(default=None, min_length=1, max_length=80)
    communicationPreference: CommunicationPreference | None = None
    individualProfile: IndividualProfileIn | None = None
    organisationProfile: OrganisationProfileIn | None = None
    status: str | None = None
    onboardingState: str | None = None
    reason: str | None = None

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in CLIENT_STATUSES:
            raise ValueError(f"status must be one of {CLIENT_STATUSES}")
        return value

    @field_validator("onboardingState")
    @classmethod
    def check_onboarding_state(cls, value: str | None) -> str | None:
        if value is not None and value not in CLIENT_ONBOARDING_STATES:
            raise ValueError(f"onboardingState must be one of {CLIENT_ONBOARDING_STATES}")
        return value

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _phone_validator("mobile")(value)


class ClientStatusUpdate(BaseModel):
    status: str
    _check = field_validator("status")(_enum_validator(CLIENT_STATUSES, "status"))


class ClientOnboardingStateUpdate(BaseModel):
    onboardingState: str
    reason: str | None = None
    _check = field_validator("onboardingState")(
        _enum_validator(CLIENT_ONBOARDING_STATES, "onboardingState")
    )


class ClientDuplicateMatchOut(BaseModel):
    client: ClientOut
    matchedOn: list[str]


class ClientDuplicateCheckRequest(BaseModel):
    # A JSON body rather than query params -- this carries a person's
    # name/mobile/email, which shouldn't end up in URL query strings
    # (access logs, proxy logs, browser history) on every debounced
    # keystroke while filling in the onboarding wizard.
    name: str = ""
    mobile: str = ""
    email: str = ""
    registrationNumber: str = ""


# --- child records -------------------------------------------------------


class ClientContactOut(BaseModel):
    id: str
    clientId: str
    name: str
    contactType: str
    mobile: str
    email: EmailStr
    isAuthorisedRepresentative: bool

    @staticmethod
    def from_model(contact) -> "ClientContactOut":
        return ClientContactOut(
            id=f"CTC-{contact.id:03d}",
            clientId=f"CLT-{contact.client_id:03d}",
            name=contact.name,
            contactType=contact.contact_type,
            mobile=contact.mobile,
            email=contact.email,
            isAuthorisedRepresentative=contact.is_authorised_representative,
        )


class ClientContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contactType: str
    mobile: str = Field(min_length=1, max_length=30)
    email: EmailStr
    isAuthorisedRepresentative: bool = False
    _check = field_validator("contactType")(_enum_validator(CONTACT_TYPES, "contactType"))
    _check_mobile = field_validator("mobile")(_phone_validator("mobile"))


class ClientContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    contactType: str | None = None
    mobile: str | None = Field(default=None, min_length=1, max_length=30)
    email: EmailStr | None = None
    isAuthorisedRepresentative: bool | None = None

    @field_validator("contactType")
    @classmethod
    def check_contact_type(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTACT_TYPES:
            raise ValueError(f"contactType must be one of {CONTACT_TYPES}")
        return value

    @field_validator("mobile")
    @classmethod
    def check_mobile(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _phone_validator("mobile")(value)


class ClientAddressOut(BaseModel):
    id: str
    clientId: str
    addressType: str
    country: str
    state: str
    city: str
    area: str | None
    street: str | None
    building: str | None

    @staticmethod
    def from_model(address) -> "ClientAddressOut":
        return ClientAddressOut(
            id=f"ADR-{address.id:03d}",
            clientId=f"CLT-{address.client_id:03d}",
            addressType=address.address_type,
            country=address.country,
            state=address.state,
            city=address.city,
            area=address.area,
            street=address.street,
            building=address.building,
        )


class ClientAddressCreate(BaseModel):
    addressType: str
    country: str = Field(min_length=1, max_length=80)
    state: str = Field(min_length=1, max_length=80)
    city: str = Field(min_length=1, max_length=80)
    area: str | None = Field(default=None, max_length=120)
    street: str | None = Field(default=None, max_length=150)
    building: str | None = Field(default=None, max_length=120)
    _check = field_validator("addressType")(_enum_validator(ADDRESS_TYPES, "addressType"))


class ClientAddressUpdate(BaseModel):
    addressType: str | None = None
    country: str | None = Field(default=None, min_length=1, max_length=80)
    state: str | None = Field(default=None, min_length=1, max_length=80)
    city: str | None = Field(default=None, min_length=1, max_length=80)
    area: str | None = Field(default=None, max_length=120)
    street: str | None = Field(default=None, max_length=150)
    building: str | None = Field(default=None, max_length=120)

    @field_validator("addressType")
    @classmethod
    def check_address_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ADDRESS_TYPES:
            raise ValueError(f"addressType must be one of {ADDRESS_TYPES}")
        return value


class ClientIdentificationOut(BaseModel):
    id: str
    clientId: str
    documentType: str
    documentNumber: str
    issueDate: date
    expiryDate: date
    issuingCountry: str

    @staticmethod
    def from_model(identification) -> "ClientIdentificationOut":
        return ClientIdentificationOut(
            id=f"IDN-{identification.id:03d}",
            clientId=f"CLT-{identification.client_id:03d}",
            documentType=identification.document_type,
            documentNumber=identification.document_number,
            issueDate=identification.issue_date,
            expiryDate=identification.expiry_date,
            issuingCountry=identification.issuing_country,
        )


class ClientIdentificationCreate(BaseModel):
    documentType: str
    documentNumber: str = Field(min_length=1, max_length=60)
    issueDate: date
    expiryDate: date
    issuingCountry: str = Field(min_length=1, max_length=80)
    _check = field_validator("documentType")(_enum_validator(IDENTIFICATION_TYPES, "documentType"))
    _check_issue_date = field_validator("issueDate")(_not_future_validator("issueDate"))

    @field_validator("expiryDate")
    @classmethod
    def expiry_after_issue(cls, value: date, info) -> date:
        issue_date = info.data.get("issueDate")
        if issue_date is not None and value <= issue_date:
            raise ValueError("expiryDate must be after issueDate")
        return value


class ClientIdentificationUpdate(BaseModel):
    documentType: str | None = None
    documentNumber: str | None = Field(default=None, min_length=1, max_length=60)
    issueDate: date | None = None
    expiryDate: date | None = None
    issuingCountry: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("documentType")
    @classmethod
    def check_document_type(cls, value: str | None) -> str | None:
        if value is not None and value not in IDENTIFICATION_TYPES:
            raise ValueError(f"documentType must be one of {IDENTIFICATION_TYPES}")
        return value

    @field_validator("issueDate")
    @classmethod
    def check_issue_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("issueDate cannot be in the future")
        return value

    @field_validator("expiryDate")
    @classmethod
    def check_expiry_after_issue(cls, value: date | None, info) -> date | None:
        issue_date = info.data.get("issueDate")
        if value is not None and issue_date is not None and value <= issue_date:
            raise ValueError("expiryDate must be after issueDate")
        return value


class ClientConsentOut(BaseModel):
    id: str
    clientId: str
    consentType: str
    version: str
    granted: bool
    dateTime: datetime
    method: str
    recordedBy: str

    @staticmethod
    def from_model(consent, recorded_by_name: str) -> "ClientConsentOut":
        return ClientConsentOut(
            id=f"CNS-{consent.id:03d}",
            clientId=f"CLT-{consent.client_id:03d}",
            consentType=consent.consent_type,
            version=consent.version,
            granted=consent.granted,
            dateTime=consent.recorded_at,
            method=consent.method,
            recordedBy=recorded_by_name,
        )


class ClientConsentCreate(BaseModel):
    consentType: str
    version: str = Field(min_length=1, max_length=20)
    granted: bool
    method: str = Field(min_length=1, max_length=150)
    _check = field_validator("consentType")(_enum_validator(CONSENT_TYPES, "consentType"))


class ClientDocumentOut(BaseModel):
    id: str
    clientId: str
    category: str
    title: str
    issueDate: date | None = None
    expiryDate: date | None = None
    issuingAuthority: str | None = None
    version: int
    verificationStatus: str
    uploadedBy: str
    uploadDate: datetime
    originalFilename: str
    fileSize: str

    @staticmethod
    def from_model(document, uploaded_by_name: str, file_size_display: str) -> "ClientDocumentOut":
        return ClientDocumentOut(
            id=f"CDOC-{document.id:03d}",
            clientId=f"CLT-{document.client_id:03d}",
            category=document.category,
            title=document.title,
            issueDate=document.issue_date,
            expiryDate=document.expiry_date,
            issuingAuthority=document.issuing_authority,
            version=document.version,
            verificationStatus=document.verification_status,
            uploadedBy=uploaded_by_name,
            uploadDate=document.upload_date,
            originalFilename=document.original_filename,
            fileSize=file_size_display,
        )


# Note: client documents are created via multipart/form-data (see
# POST /api/clients/{client_id}/documents in app/api/clients.py, which takes
# Form(...)/File(...) params directly) so there is no JSON create schema
# here -- same pattern as app/schemas/document.py's DocumentOut/create route.
# Metadata-only edits (no re-upload) go through this plain JSON schema instead.


class ClientDocumentUpdate(BaseModel):
    category: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=150)
    issueDate: date | None = None
    expiryDate: date | None = None
    issuingAuthority: str | None = Field(default=None, max_length=150)

    @field_validator("category")
    @classmethod
    def check_category(cls, value: str | None) -> str | None:
        if value is not None and value not in CLIENT_DOCUMENT_CATEGORIES:
            raise ValueError(f"category must be one of {CLIENT_DOCUMENT_CATEGORIES}")
        return value


class ClientVerificationOut(BaseModel):
    id: str
    clientId: str
    item: str
    result: str
    verifiedBy: str
    verifiedDate: datetime
    notes: str | None = None
    documentId: str | None = None

    @staticmethod
    def from_model(verification, verified_by_name: str) -> "ClientVerificationOut":
        return ClientVerificationOut(
            id=f"VER-{verification.id:03d}",
            clientId=f"CLT-{verification.client_id:03d}",
            item=verification.item,
            result=verification.result,
            verifiedBy=verified_by_name,
            verifiedDate=verification.verified_date,
            notes=verification.notes,
            documentId=f"CDOC-{verification.document_id:03d}" if verification.document_id else None,
        )


class ClientVerificationCreate(BaseModel):
    item: str = Field(min_length=1, max_length=150)
    result: str
    notes: str | None = Field(default=None, max_length=1000)
    documentId: str | None = None
    _check = field_validator("result")(_enum_validator(CLIENT_VERIFICATION_RESULTS, "result"))
