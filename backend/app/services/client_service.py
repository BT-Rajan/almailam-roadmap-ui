import re
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    CLIENT_ONBOARDING_ALLOWED_TRANSITIONS,
    CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.client import (
    Client,
    ClientAddress,
    ClientConsent,
    ClientContact,
    ClientDocument,
    ClientIdentification,
    ClientVerification,
)
from app.services import audit_service

ENTITY_TYPE = "CLIENT"


def parse_client_id(raw: str) -> int:
    text = raw.removeprefix("CLT-") if raw.upper().startswith("CLT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid client id.")
    return int(text)


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


CLIENT_SORTABLE_FIELDS = {
    "companyName": Client.company_name,
    "contactPerson": Client.contact_person,
    "clientType": Client.client_type,
    "status": Client.status,
    "onboardingState": Client.onboarding_state,
}


def list_clients(
    db: Session,
    search: str | None = None,
    client_type: str | None = None,
    status: str | None = None,
    onboarding_state: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    query = db.query(Client).filter(Client.deleted_at.is_(None))

    if search:
        term = f"%{search.strip().lower()}%"
        digits = _digits(search)
        conditions = [
            Client.company_name.ilike(term),
            Client.contact_person.ilike(term),
            Client.email.ilike(term),
        ]
        if digits:
            conditions.append(Client.mobile.contains(digits))
        query = query.filter(or_(*conditions))

    if client_type:
        query = query.filter(Client.client_type == client_type)
    if status:
        query = query.filter(Client.status == status)
    if onboarding_state:
        query = query.filter(Client.onboarding_state == onboarding_state)

    return sort_and_paginate(query, Client, CLIENT_SORTABLE_FIELDS, sort, page, page_size)


def get_client(db: Session, client_id: int) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.deleted_at.is_(None)).first()
    if client is None:
        raise NotFoundError("Client")
    return client


def create_client(db: Session, payload, user_id: int | None) -> Client:
    client = Client(
        client_type=payload.clientType,
        company_name=payload.companyName,
        contact_person=payload.contactPerson,
        mobile=payload.mobile,
        email=payload.email,
        city=payload.city,
        preferred_language=payload.communicationPreference.preferredLanguage,
        preferred_channel=payload.communicationPreference.preferredChannel,
        email_consent=payload.communicationPreference.emailConsent,
        whatsapp_consent=payload.communicationPreference.whatsappConsent,
        sms_consent=payload.communicationPreference.smsConsent,
    )
    if payload.individualProfile:
        p = payload.individualProfile
        client.ind_full_legal_name = p.fullLegalName
        client.ind_preferred_name = p.preferredName
        client.ind_nationality = p.nationality
        client.ind_date_of_birth = p.dateOfBirth
        client.ind_country_of_residence = p.countryOfResidence
    if payload.organisationProfile:
        p = payload.organisationProfile
        client.org_legal_name = p.legalName
        client.org_trade_name = p.tradeName
        client.org_organisation_type = p.organisationType
        client.org_registration_number = p.registrationNumber
        client.org_trade_licence_number = p.tradeLicenceNumber
        client.org_tax_identification_number = p.taxIdentificationNumber
        client.org_country_of_registration = p.countryOfRegistration
        client.org_date_of_incorporation = p.dateOfIncorporation
        client.org_website = p.website

    db.add(client)
    db.flush()  # assign client.id before the audit row references it
    audit_service.log_event(db, ENTITY_TYPE, client.id, "Client created", user_id, new_value=client.company_name)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client_id: int, payload, user_id: int | None) -> Client:
    client = get_client(db, client_id)
    field_map = {
        "companyName": ("company_name", None),
        "contactPerson": ("contact_person", None),
        "mobile": ("mobile", None),
        "email": ("email", None),
        "city": ("city", None),
    }
    changes: dict[str, tuple] = {}
    for api_field, (attr, _) in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(client, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(client, attr, value)

    if payload.communicationPreference is not None:
        cp = payload.communicationPreference
        client.preferred_language = cp.preferredLanguage
        client.preferred_channel = cp.preferredChannel
        client.email_consent = cp.emailConsent
        client.whatsapp_consent = cp.whatsappConsent
        client.sms_consent = cp.smsConsent

    audit_service.log_field_changes(db, ENTITY_TYPE, client.id, changes, user_id)
    db.commit()
    db.refresh(client)
    return client


def set_status(db: Session, client_id: int, status: str, user_id: int | None) -> Client:
    client = get_client(db, client_id)
    if client.status != status:
        audit_service.log_event(
            db, ENTITY_TYPE, client.id, "Status changed", user_id,
            previous_value=client.status, new_value=status,
        )
        client.status = status
        db.commit()
        db.refresh(client)
    return client


def set_onboarding_state(
    db: Session, client_id: int, new_state: str, reason: str | None, user_id: int | None
) -> Client:
    client = get_client(db, client_id)
    assert_transition_allowed(
        CLIENT_ONBOARDING_ALLOWED_TRANSITIONS, client.onboarding_state, new_state, "client"
    )
    if new_state in CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON:
        assert_reason_given(reason, f"A reason is required to move onboarding to '{new_state}'.")

    audit_service.log_event(
        db, ENTITY_TYPE, client.id, "Onboarding state changed", user_id,
        previous_value=client.onboarding_state, new_value=new_state, reason=reason,
    )
    client.onboarding_state = new_state
    db.commit()
    db.refresh(client)
    return client


def get_audit_events(db: Session, client_id: int) -> list[dict]:
    get_client(db, client_id)  # 404 if the client doesn't exist
    return audit_service.get_history(db, ENTITY_TYPE, client_id)


def find_possible_duplicates(db: Session, name: str, mobile: str, email: str) -> list[dict]:
    name_term = name.strip().lower()
    mobile_digits = _digits(mobile)
    email_term = email.strip().lower()

    matches: list[dict] = []
    for client in db.query(Client).filter(Client.deleted_at.is_(None)).all():
        matched_on: list[str] = []
        if len(name_term) > 2 and name_term in client.company_name.lower():
            matched_on.append("Name")
        if len(mobile_digits) >= 7 and _digits(client.mobile) == mobile_digits:
            matched_on.append("Mobile number")
        if len(email_term) > 3 and client.email.lower() == email_term:
            matched_on.append("Email")
        if matched_on:
            matches.append({"client": client, "matchedOn": matched_on})
    return matches


# --- child records -----------------------------------------------------


def list_contacts(db: Session, client_id: int) -> list[ClientContact]:
    return (
        db.query(ClientContact)
        .filter(ClientContact.client_id == client_id)
        .order_by(ClientContact.id.asc())
        .all()
    )


def create_contact(db: Session, client_id: int, payload) -> ClientContact:
    get_client(db, client_id)
    contact = ClientContact(
        client_id=client_id,
        name=payload.name,
        contact_type=payload.contactType,
        mobile=payload.mobile,
        email=payload.email,
        is_authorised_representative=payload.isAuthorisedRepresentative,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def list_addresses(db: Session, client_id: int) -> list[ClientAddress]:
    return (
        db.query(ClientAddress)
        .filter(ClientAddress.client_id == client_id)
        .order_by(ClientAddress.id.asc())
        .all()
    )


def create_address(db: Session, client_id: int, payload) -> ClientAddress:
    get_client(db, client_id)
    address = ClientAddress(
        client_id=client_id,
        address_type=payload.addressType,
        country=payload.country,
        state=payload.state,
        city=payload.city,
        area=payload.area,
        street=payload.street,
        building=payload.building,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def list_identifications(db: Session, client_id: int) -> list[ClientIdentification]:
    return (
        db.query(ClientIdentification)
        .filter(ClientIdentification.client_id == client_id)
        .order_by(ClientIdentification.id.asc())
        .all()
    )


def create_identification(db: Session, client_id: int, payload) -> ClientIdentification:
    get_client(db, client_id)
    identification = ClientIdentification(
        client_id=client_id,
        document_type=payload.documentType,
        document_number=payload.documentNumber,
        issue_date=payload.issueDate,
        expiry_date=payload.expiryDate,
        issuing_country=payload.issuingCountry,
    )
    db.add(identification)
    db.commit()
    db.refresh(identification)
    return identification


def list_consents(db: Session, client_id: int) -> list[ClientConsent]:
    return (
        db.query(ClientConsent)
        .filter(ClientConsent.client_id == client_id)
        .order_by(ClientConsent.id.asc())
        .all()
    )


def create_consent(db: Session, client_id: int, payload, recorded_by: int) -> ClientConsent:
    get_client(db, client_id)
    consent = ClientConsent(
        client_id=client_id,
        consent_type=payload.consentType,
        version=payload.version,
        granted=payload.granted,
        recorded_at=datetime.now(timezone.utc),
        method=payload.method,
        recorded_by=recorded_by,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def list_documents(db: Session, client_id: int) -> list[ClientDocument]:
    return (
        db.query(ClientDocument)
        .filter(ClientDocument.client_id == client_id)
        .order_by(ClientDocument.id.desc())
        .all()
    )


def create_document(db: Session, client_id: int, payload, uploaded_by: int) -> ClientDocument:
    get_client(db, client_id)
    document = ClientDocument(
        client_id=client_id,
        category=payload.category,
        title=payload.title,
        issue_date=payload.issueDate,
        expiry_date=payload.expiryDate,
        issuing_authority=payload.issuingAuthority,
        version=1,
        verification_status="Pending",
        uploaded_by=uploaded_by,
        upload_date=datetime.now(timezone.utc),
    )
    db.add(document)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, client_id, "Document uploaded", uploaded_by, new_value=document.title)
    db.commit()
    db.refresh(document)
    return document


def list_verifications(db: Session, client_id: int) -> list[ClientVerification]:
    return (
        db.query(ClientVerification)
        .filter(ClientVerification.client_id == client_id)
        .order_by(ClientVerification.id.desc())
        .all()
    )


def delete_client(db: Session, client_id: int, actor_id: int) -> None:
    client = get_client(db, client_id)
    audit_service.log_event(db, ENTITY_TYPE, client.id, "Client deleted", actor_id, previous_value=client.company_name)
    client.deleted_at = datetime.now(timezone.utc)
    db.commit()
