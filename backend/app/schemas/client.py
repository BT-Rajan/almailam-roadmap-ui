from datetime import date, datetime

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


# --- nested profile schemas -------------------------------------------------


class IndividualProfileIn(BaseModel):
    fullLegalName: str = Field(max_length=150)
    preferredName: str | None = Field(default=None, max_length=100)
    nationality: str = Field(max_length=80)
    dateOfBirth: date
    countryOfResidence: str = Field(max_length=80)


class IndividualProfileOut(BaseModel):
    fullLegalName: str
    preferredName: str | None
    nationality: str
    dateOfBirth: date
    countryOfResidence: str


class OrganisationProfileIn(BaseModel):
    legalName: str = Field(max_length=200)
    tradeName: str | None = Field(default=None, max_length=200)
    organisationType: str = Field(max_length=100)
    registrationNumber: str = Field(max_length=60)
    tradeLicenceNumber: str | None = Field(default=None, max_length=60)
    taxIdentificationNumber: str | None = Field(default=None, max_length=60)
    countryOfRegistration: str = Field(max_length=80)
    dateOfIncorporation: date
    website: str | None = Field(default=None, max_length=200)


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

    @field_validator("organisationProfile")
    @classmethod
    def profile_matches_type(cls, value, info):
        client_type = info.data.get("clientType")
        if client_type == "Individual" and value is not None:
            raise ValueError("organisationProfile must not be set when clientType is Individual")
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

    @field_validator("expiryDate")
    @classmethod
    def expiry_after_issue(cls, value: date, info) -> date:
        issue_date = info.data.get("issueDate")
        if issue_date is not None and value <= issue_date:
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

    @staticmethod
    def from_model(document, uploaded_by_name: str) -> "ClientDocumentOut":
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
        )


class ClientDocumentCreate(BaseModel):
    category: str
    title: str = Field(min_length=1, max_length=150)
    issueDate: date | None = None
    expiryDate: date | None = None
    issuingAuthority: str | None = Field(default=None, max_length=150)
    _check = field_validator("category")(_enum_validator(CLIENT_DOCUMENT_CATEGORIES, "category"))


class ClientVerificationOut(BaseModel):
    id: str
    clientId: str
    item: str
    result: str
    verifiedBy: str
    verifiedDate: datetime
    notes: str | None = None

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
        )
