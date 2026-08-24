import re
from datetime import date, datetime, timedelta, timezone

from fastapi import UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.pagination import DEFAULT_PAGE_SIZE, sort_and_paginate
from app.core.status_transitions import (
    CLIENT_ONBOARDING_ALLOWED_TRANSITIONS,
    CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON,
)
from app.core.workflow import assert_reason_given, assert_transition_allowed
from app.models.user import User
from app.models.project import Project
from app.models.client import (
    CLIENT_DOCUMENT_CATEGORIES,
    CLIENT_VERIFICATION_RESULTS,
    Client,
    ClientAddress,
    ClientConsent,
    ClientContact,
    ClientDocument,
    ClientDocumentVersion,
    ClientIdentification,
    ClientVerification,
)
from app.services import audit_service, company_service, notification_service

ENTITY_TYPE = "CLIENT"


def parse_client_id(raw: str) -> int:
    text = raw.removeprefix("CLT-") if raw.upper().startswith("CLT-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid client id.")
    return int(text)


def _parse_prefixed_id(raw: str, prefix: str, label: str) -> int:
    text = raw.removeprefix(prefix) if raw.upper().startswith(prefix) else raw
    if not text.isdigit():
        raise ValidationAppError(f"Invalid {label} id.")
    return int(text)


def parse_prefixed_id(raw: str, prefix: str, label: str) -> int:
    """Public wrapper for API-layer routes that need to parse a child
    record id (e.g. "CTC-001" -> 1) without duplicating this logic."""
    return _parse_prefixed_id(raw, prefix, label)


def parse_document_id(raw: str) -> int:
    return _parse_prefixed_id(raw, "CDOC-", "document")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _parse_optional_date(value: str | None, label: str) -> date | None:
    if value is None or value.strip() == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationAppError(f"{label} must be a valid date (YYYY-MM-DD).") from exc


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
    account_manager_id: str | None = None,
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
    if account_manager_id:
        query = query.filter(Client.account_manager_id == parse_prefixed_id(account_manager_id, "USR-", "user"))

    return sort_and_paginate(query, Client, CLIENT_SORTABLE_FIELDS, sort, page, page_size)


def get_client(db: Session, client_id: int) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.deleted_at.is_(None)).first()
    if client is None:
        raise NotFoundError("Client")
    return client


def _lock_client(db: Session, client_id: int) -> Client:
    """Same as get_client() but takes a row lock -- used before a
    check-then-insert duplicate check (contacts, identifications) so two
    concurrent requests for the same client can't both pass the check and
    both insert. Scoped to a single client row, so it doesn't serialize
    unrelated clients' requests against each other."""
    client = db.query(Client).filter(Client.id == client_id, Client.deleted_at.is_(None)).with_for_update().first()
    if client is None:
        raise NotFoundError("Client")
    return client


def _resolve_account_manager_id(db: Session, raw: str | None) -> int | None:
    """None = leave untouched (caller's responsibility not to call this),
    "" = unassign, a real "USR-XXX" id = assign (validated to exist)."""
    if raw is None or raw.strip() == "":
        return None
    user_id = parse_prefixed_id(raw, "USR-", "user")
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True)).first()
    if user is None:
        raise ValidationAppError("accountManagerId does not refer to a known user.")
    return user.id


def create_client(db: Session, payload, user_id: int | None) -> Client:
    client = Client(
        client_type=payload.clientType,
        company_name=payload.companyName,
        contact_person=payload.contactPerson,
        mobile=payload.mobile,
        email=payload.email,
        city=payload.city,
        # New clients go straight to "Ready" instead of starting the
        # multi-step onboarding pipeline (Information Required ->
        # Documents Required -> Under Review) -- the New Client wizard
        # already requires full contact, address, identification and
        # consent details up front, so there is nothing left for that
        # pipeline to gate. They can be selected on a project immediately
        # (see project_service.create_project's onboarding_state ==
        # "Ready" check). Staff can still move a client to any of the
        # review states manually afterwards via "Change Status" on the
        # client workspace page if something needs a closer look.
        onboarding_state="Ready",
        preferred_language=payload.communicationPreference.preferredLanguage,
        preferred_channel=payload.communicationPreference.preferredChannel,
        email_consent=payload.communicationPreference.emailConsent,
        whatsapp_consent=payload.communicationPreference.whatsappConsent,
        sms_consent=payload.communicationPreference.smsConsent,
        notes=payload.notes.strip() if payload.notes and payload.notes.strip() else None,
    )
    if payload.accountManagerId:
        client.account_manager_id = _resolve_account_manager_id(db, payload.accountManagerId)
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

    if payload.individualProfile is not None:
        if client.client_type != "Individual":
            raise ValidationAppError("This client is not an Individual; cannot set individualProfile.")
        p = payload.individualProfile
        profile_map = {
            "ind_full_legal_name": p.fullLegalName,
            "ind_preferred_name": p.preferredName,
            "ind_nationality": p.nationality,
            "ind_date_of_birth": p.dateOfBirth,
            "ind_country_of_residence": p.countryOfResidence,
        }
        for attr, value in profile_map.items():
            old = getattr(client, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(client, attr, value)

        if client.company_name != p.fullLegalName:
            changes["company_name"] = (client.company_name, p.fullLegalName)
        client.company_name = p.fullLegalName

    if payload.organisationProfile is not None:
        if client.client_type == "Individual":
            raise ValidationAppError("This client is an Individual; cannot set organisationProfile.")
        p = payload.organisationProfile
        profile_map = {
            "org_legal_name": p.legalName,
            "org_trade_name": p.tradeName,
            "org_organisation_type": p.organisationType,
            "org_registration_number": p.registrationNumber,
            "org_trade_licence_number": p.tradeLicenceNumber,
            "org_tax_identification_number": p.taxIdentificationNumber,
            "org_country_of_registration": p.countryOfRegistration,
            "org_date_of_incorporation": p.dateOfIncorporation,
            "org_website": p.website,
        }
        for attr, value in profile_map.items():
            old = getattr(client, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(client, attr, value)

        # company_name is a denormalized copy of the profile's legal name,
        # used directly by search (list_clients) and duplicate detection
        # (find_possible_duplicates) -- keep it in sync whenever the real
        # source of truth changes, or those would silently start working
        # off a stale name after any edit.
        if client.company_name != p.legalName:
            changes["company_name"] = (client.company_name, p.legalName)
        client.company_name = p.legalName

    if payload.communicationPreference is not None:
        cp = payload.communicationPreference
        client.preferred_language = cp.preferredLanguage
        client.preferred_channel = cp.preferredChannel
        client.email_consent = cp.emailConsent
        client.whatsapp_consent = cp.whatsappConsent
        client.sms_consent = cp.smsConsent

    if payload.accountManagerId is not None:
        new_manager_id = _resolve_account_manager_id(db, payload.accountManagerId)
        if client.account_manager_id != new_manager_id:
            changes["account_manager_id"] = (client.account_manager_id, new_manager_id)
        client.account_manager_id = new_manager_id

    if payload.notes is not None:
        new_notes = payload.notes.strip() or None
        if client.notes != new_notes:
            changes["notes"] = (client.notes, new_notes)
        client.notes = new_notes

    audit_service.log_field_changes(db, ENTITY_TYPE, client.id, changes, user_id)
    db.commit()
    db.refresh(client)

    if payload.status is not None and payload.status != client.status:
        client = set_status(db, client_id, payload.status, user_id)
    if payload.onboardingState is not None and payload.onboardingState != client.onboarding_state:
        client = set_onboarding_state(db, client_id, payload.onboardingState, payload.reason, user_id)

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
    # A fresh staleness period starts now that onboarding has genuinely
    # moved -- see check_and_notify_stale_onboarding.
    client.onboarding_notified_at = None
    db.commit()
    db.refresh(client)
    return client


def auto_advance_onboarding(db: Session, client_id: int, user_id: int | None) -> Client:
    """Walks a client forward through every onboarding transition that
    has exactly one legal next state, stopping the moment it reaches a
    genuine decision point (a state with zero or multiple valid next
    states -- e.g. "Under Review" branching to Ready/Rejected/Documents
    Required) or a state requiring a reason (which needs a human to
    supply one).

    This exists because walking a fully-ready client from "Information
    Required" all the way to "Under Review" previously took three
    separate manual round trips through the status-change dialog, even
    though none of those three hops involve any real decision -- each
    one only ever has a single legal destination. Each hop still goes
    through the exact same validation and audit logging as a single
    set_onboarding_state() call (so the audit trail shows the real
    sequence of transitions, not one opaque jump); this just removes
    the repeated manual clicking between them.

    Not gated on document/verification completeness -- staff can
    already manually force any individual transition via "Change
    Status" regardless of what's actually on file, so this doesn't
    introduce a stricter rule than what already exists; it only
    automates the mechanical part.
    """
    client = get_client(db, client_id)
    hops = 0
    while True:
        options = CLIENT_ONBOARDING_ALLOWED_TRANSITIONS.get(client.onboarding_state, set())
        if len(options) != 1:
            break
        next_state = next(iter(options))
        if next_state in CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON:
            break
        client = set_onboarding_state(db, client_id, next_state, None, user_id)
        hops += 1
    return client


def check_and_notify_stale_onboarding(db: Session) -> int:
    """Finds clients whose onboarding hasn't moved in more than the
    admin-configurable threshold (CompanySettings.
    stale_onboarding_alert_days, default 5) and notifies the account
    manager once per staleness episode -- mirrors project_service.
    check_and_notify_stale_projects exactly, applied to onboarding
    instead of project stage. onboarding_notified_at prevents
    re-notifying every time this runs, and is cleared the moment
    onboarding_state actually changes (set_onboarding_state), so a
    fresh staleness period starts if it stalls again later at a
    different step.

    Only considers clients still genuinely in progress -- Ready,
    Rejected, and Suspended are all deliberate end states (done,
    declined, or intentionally paused) that don't need a "you forgot
    about this" nudge. A client with no account manager assigned is
    skipped: there's no one specific to notify.

    Called by the same scheduled job as check_and_notify_stale_projects
    (see main.py) rather than a second one -- one background job doing
    two related checks, not two nearly-identical jobs.
    """
    IN_PROGRESS_STATES = ("Information Required", "Documents Required", "Under Review")

    settings = company_service.get_settings(db)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=settings.stale_onboarding_alert_days)

    candidates = (
        db.query(Client)
        .filter(
            Client.deleted_at.is_(None),
            Client.onboarding_state.in_(IN_PROGRESS_STATES),
            Client.onboarding_notified_at.is_(None),
            Client.account_manager_id.isnot(None),
        )
        .all()
    )

    notified_count = 0
    for client in candidates:
        last_change = audit_service.get_last_event_time(db, ENTITY_TYPE, client.id, "Onboarding state changed")
        reference_time = last_change if last_change else client.created_at

        if reference_time <= cutoff:
            notification_service.create_notification(
                db, client.account_manager_id,
                "Client onboarding hasn't moved in a while",
                f"{client.company_name} has been at '{client.onboarding_state}' for more than "
                f"{settings.stale_onboarding_alert_days} days without advancing.",
                "System",
            )
            client.onboarding_notified_at = datetime.now(timezone.utc)
            notified_count += 1

    db.commit()
    return notified_count


def _client_exists(db: Session, client_id: int) -> None:
    """Like get_client() but doesn't exclude soft-deleted clients -- used
    only for read-only historical views (audit trail) where a merged-away
    client's own history must remain inspectable. Everything else
    (updates, child-record creation, etc.) should keep using get_client()
    so a soft-deleted client stays fully locked for writes."""
    exists = db.query(Client.id).filter(Client.id == client_id).first()
    if exists is None:
        raise NotFoundError("Client")


def get_audit_events(db: Session, client_id: int) -> list[dict]:
    _client_exists(db, client_id)  # 404 only if the client never existed at all
    return audit_service.get_history(db, ENTITY_TYPE, client_id)


def find_clients_with_matching_identification(db: Session, client_id: int) -> list[dict]:
    """Finds other (non-deleted) clients that share an identical
    (documentType, documentNumber) identification with the given client --
    the strongest duplicate signal available, since a real government-issued
    ID legitimately belongs to exactly one person or entity. This is what
    the client workspace's merge-eligibility check uses; it deliberately
    does NOT feed the free-text onboarding-wizard duplicate check (name/
    mobile/email/registration), since that runs before either client's
    identification records necessarily exist yet."""
    get_client(db, client_id)
    own_identifications = list_identifications(db, client_id)
    if not own_identifications:
        return []

    matches: dict[int, dict] = {}
    for ident in own_identifications:
        number_normalised = ident.document_number.strip().lower()
        candidates = (
            db.query(ClientIdentification)
            .join(Client, Client.id == ClientIdentification.client_id)
            .filter(
                ClientIdentification.deleted_at.is_(None),
                Client.deleted_at.is_(None),
                ClientIdentification.client_id != client_id,
                ClientIdentification.document_type == ident.document_type,
                func.lower(ClientIdentification.document_number) == number_normalised,
            )
            .all()
        )
        for candidate in candidates:
            label = f"{ident.document_type} ({ident.document_number})"
            if candidate.client_id in matches:
                matches[candidate.client_id]["matchedOn"].append(label)
            else:
                matches[candidate.client_id] = {"client": get_client(db, candidate.client_id), "matchedOn": [label]}
    return list(matches.values())


def merge_clients(db: Session, source_client_id: int, target_client_id: int, user_id: int | None) -> Client:
    """Merges `source` into `target`: moves every child record (skipping
    any that would collide with something already on the target, e.g. a
    contact with the same mobile number already present there), reassigns
    the source's projects to the target, preserves the source's own
    contact identity as a plain contact if it isn't already represented,
    fills a few gaps on the target from the source (account manager,
    notes), and soft-deletes the source. Intentionally does NOT hard-
    delete anything -- the source client row and every record that didn't
    move stay in the database, just no longer reachable through the app,
    so this can be investigated or reversed by a database administrator
    if it turns out to be a mistake."""
    if source_client_id == target_client_id:
        raise ValidationAppError("Cannot merge a client into itself.")

    source = get_client(db, source_client_id)
    target = get_client(db, target_client_id)

    if source.client_type != target.client_type:
        raise ValidationAppError(
            f"Cannot merge: '{source.company_name}' is {source.client_type} but "
            f"'{target.company_name}' is {target.client_type}."
        )

    for contact in list_contacts(db, source_client_id):
        mobile_digits = _digits(contact.mobile)
        email_lower = contact.email.strip().lower()
        conflict = any(
            _digits(existing.mobile) == mobile_digits or existing.email.strip().lower() == email_lower
            for existing in list_contacts(db, target_client_id)
        )
        if not conflict:
            contact.client_id = target_client_id

    for address in list_addresses(db, source_client_id):
        address.client_id = target_client_id

    for identification in list_identifications(db, source_client_id):
        number_normalised = identification.document_number.strip().lower()
        conflict = any(
            existing.document_type == identification.document_type
            and existing.document_number.strip().lower() == number_normalised
            for existing in list_identifications(db, target_client_id)
        )
        if not conflict:
            identification.client_id = target_client_id

    for document in list_documents(db, source_client_id):
        document.client_id = target_client_id

    for verification in list_verifications(db, source_client_id):
        verification.client_id = target_client_id

    for consent in list_consents(db, source_client_id):
        consent.client_id = target_client_id

    from app.models.project import Project

    moved_projects = (
        db.query(Project).filter(Project.client_id == source_client_id, Project.deleted_at.is_(None)).all()
    )
    for project in moved_projects:
        project.client_id = target_client_id

    # The source's own top-level contact details (contactPerson/mobile/
    # email) represent a real person too -- preserve them as a plain
    # contact on the target if nothing already moved covers the same
    # mobile/email, rather than silently losing that identity.
    mobile_digits = _digits(source.mobile)
    email_lower = source.email.strip().lower()
    already_represented = any(
        _digits(c.mobile) == mobile_digits or c.email.strip().lower() == email_lower
        for c in list_contacts(db, target_client_id)
    )
    if not already_represented:
        db.add(
            ClientContact(
                client_id=target_client_id,
                name=source.contact_person,
                contact_type="Other",
                mobile=source.mobile,
                email=source.email,
                is_authorised_representative=False,
            )
        )

    if not target.account_manager_id and source.account_manager_id:
        target.account_manager_id = source.account_manager_id

    source_code = f"CLT-{source.id:03d}"
    target_code = f"CLT-{target.id:03d}"
    if source.notes:
        merged_note = f"[Merged from {source_code} ({source.company_name})]: {source.notes}"
        target.notes = f"{target.notes}\n\n{merged_note}" if target.notes else merged_note

    audit_service.log_event(
        db, ENTITY_TYPE, target.id, "Client merged", user_id,
        new_value=f"Merged {source_code} ({source.company_name}) into this client",
    )
    audit_service.log_event(
        db, ENTITY_TYPE, source.id, "Client merged into another client", user_id,
        new_value=f"Merged into {target_code} ({target.company_name})",
    )

    source.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(target)
    return target


def find_possible_duplicates(
    db: Session, name: str, mobile: str, email: str, registration_number: str = ""
) -> list[dict]:
    name_term = name.strip().lower()
    mobile_digits = _digits(mobile)
    email_term = email.strip().lower()
    reg_term = registration_number.strip().lower()

    # Name/email/registration have no formatting ambiguity, so they can be
    # filtered reliably in SQL rather than loading every client row on
    # every debounced keystroke while filling in the onboarding wizard.
    sql_conditions = []
    if len(name_term) > 2:
        sql_conditions.append(func.lower(Client.company_name).contains(name_term))
    if len(email_term) > 3:
        sql_conditions.append(func.lower(Client.email) == email_term)
    if reg_term:
        sql_conditions.append(func.lower(Client.org_registration_number) == reg_term)
        sql_conditions.append(func.lower(Client.org_trade_licence_number) == reg_term)

    candidates: dict[int, Client] = {}
    if sql_conditions:
        for client in db.query(Client).filter(Client.deleted_at.is_(None), or_(*sql_conditions)).all():
            candidates[client.id] = client

    if len(mobile_digits) >= 7:
        # Mobile numbers may be stored with inconsistent formatting
        # (spaces, dashes) depending on how they were typed, so an exact
        # SQL substring match on the raw column isn't reliable enough to
        # replace the digit-normalized comparison below -- but scanning
        # just (id, mobile) instead of full rows keeps this cheap even as
        # the client list grows, rather than hydrating every column of
        # every client just to check one field.
        mobile_rows = db.query(Client.id, Client.mobile).filter(Client.deleted_at.is_(None)).all()
        matching_ids = {client_id for client_id, stored_mobile in mobile_rows if _digits(stored_mobile) == mobile_digits}
        missing_ids = matching_ids - candidates.keys()
        if missing_ids:
            for client in db.query(Client).filter(Client.id.in_(missing_ids)).all():
                candidates[client.id] = client

    matches: list[dict] = []
    for client in candidates.values():
        matched_on: list[str] = []
        if len(name_term) > 2 and name_term in client.company_name.lower():
            matched_on.append("Name")
        if len(mobile_digits) >= 7 and _digits(client.mobile) == mobile_digits:
            matched_on.append("Mobile number")
        if len(email_term) > 3 and client.email.lower() == email_term:
            matched_on.append("Email")
        # Registration/trade licence number is the strongest duplicate
        # signal for an organisation -- two onboarding attempts for the
        # same company under a slightly different name/contact would
        # otherwise sail past the checks above entirely.
        if reg_term and client.org_registration_number and client.org_registration_number.strip().lower() == reg_term:
            matched_on.append("Registration number")
        if reg_term and client.org_trade_licence_number and client.org_trade_licence_number.strip().lower() == reg_term:
            matched_on.append("Trade licence number")
        if matched_on:
            matches.append({"client": client, "matchedOn": matched_on})
    return matches


# --- child records -----------------------------------------------------


def list_contacts(db: Session, client_id: int) -> list[ClientContact]:
    return (
        db.query(ClientContact)
        .filter(ClientContact.client_id == client_id, ClientContact.deleted_at.is_(None))
        .order_by(ClientContact.id.asc())
        .all()
    )


def get_contact(db: Session, client_id: int, contact_id: int) -> ClientContact:
    contact = (
        db.query(ClientContact)
        .filter(
            ClientContact.id == contact_id,
            ClientContact.client_id == client_id,
            ClientContact.deleted_at.is_(None),
        )
        .first()
    )
    if contact is None:
        raise NotFoundError("Contact")
    return contact


def _check_contact_duplicate(
    db: Session, client_id: int, mobile: str, email: str, exclude_id: int | None = None
) -> None:
    mobile_digits = _digits(mobile)
    email_lower = email.strip().lower()
    for existing in list_contacts(db, client_id):
        if exclude_id is not None and existing.id == exclude_id:
            continue
        if _digits(existing.mobile) == mobile_digits:
            raise ValidationAppError(f"A contact with mobile number {mobile} already exists for this client.")
        if existing.email.strip().lower() == email_lower:
            raise ValidationAppError(f"A contact with email {email} already exists for this client.")


def create_contact(db: Session, client_id: int, payload, user_id: int | None = None) -> ClientContact:
    _lock_client(db, client_id)
    _check_contact_duplicate(db, client_id, payload.mobile, payload.email)

    contact = ClientContact(
        client_id=client_id,
        name=payload.name,
        contact_type=payload.contactType,
        mobile=payload.mobile,
        email=payload.email,
        is_authorised_representative=payload.isAuthorisedRepresentative,
    )
    db.add(contact)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, client_id, "Contact added", user_id, new_value=contact.name)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, client_id: int, contact_id: int, payload, user_id: int | None) -> ClientContact:
    _lock_client(db, client_id)
    contact = get_contact(db, client_id, contact_id)

    new_mobile = payload.mobile if payload.mobile is not None else contact.mobile
    new_email = payload.email if payload.email is not None else contact.email
    if payload.mobile is not None or payload.email is not None:
        _check_contact_duplicate(db, client_id, new_mobile, new_email, exclude_id=contact_id)

    field_map = {
        "name": "name",
        "contactType": "contact_type",
        "mobile": "mobile",
        "email": "email",
        "isAuthorisedRepresentative": "is_authorised_representative",
    }
    changes: dict[str, tuple] = {}
    for api_field, attr in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(contact, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(contact, attr, value)

    audit_service.log_field_changes(db, ENTITY_TYPE, client_id, changes, user_id, label_prefix="Updated contact")
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, client_id: int, contact_id: int, user_id: int | None) -> None:
    contact = get_contact(db, client_id, contact_id)
    audit_service.log_event(db, ENTITY_TYPE, client_id, "Contact removed", user_id, previous_value=contact.name)
    contact.deleted_at = datetime.now(timezone.utc)
    db.commit()


def list_addresses(db: Session, client_id: int) -> list[ClientAddress]:
    return (
        db.query(ClientAddress)
        .filter(ClientAddress.client_id == client_id, ClientAddress.deleted_at.is_(None))
        .order_by(ClientAddress.id.asc())
        .all()
    )


def get_address(db: Session, client_id: int, address_id: int) -> ClientAddress:
    address = (
        db.query(ClientAddress)
        .filter(
            ClientAddress.id == address_id,
            ClientAddress.client_id == client_id,
            ClientAddress.deleted_at.is_(None),
        )
        .first()
    )
    if address is None:
        raise NotFoundError("Address")
    return address


def create_address(db: Session, client_id: int, payload, user_id: int | None = None) -> ClientAddress:
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
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Address added", user_id, new_value=f"{address.address_type}: {address.city}"
    )
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, client_id: int, address_id: int, payload, user_id: int | None) -> ClientAddress:
    address = get_address(db, client_id, address_id)
    field_map = {
        "addressType": "address_type",
        "country": "country",
        "state": "state",
        "city": "city",
        "area": "area",
        "street": "street",
        "building": "building",
    }
    changes: dict[str, tuple] = {}
    for api_field, attr in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(address, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(address, attr, value)

    audit_service.log_field_changes(db, ENTITY_TYPE, client_id, changes, user_id, label_prefix="Updated address")
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, client_id: int, address_id: int, user_id: int | None) -> None:
    address = get_address(db, client_id, address_id)
    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Address removed", user_id, previous_value=f"{address.address_type}: {address.city}"
    )
    address.deleted_at = datetime.now(timezone.utc)
    db.commit()


def list_identifications(db: Session, client_id: int) -> list[ClientIdentification]:
    return (
        db.query(ClientIdentification)
        .filter(ClientIdentification.client_id == client_id, ClientIdentification.deleted_at.is_(None))
        .order_by(ClientIdentification.id.asc())
        .all()
    )


def get_identification(db: Session, client_id: int, identification_id: int) -> ClientIdentification:
    identification = (
        db.query(ClientIdentification)
        .filter(
            ClientIdentification.id == identification_id,
            ClientIdentification.client_id == client_id,
            ClientIdentification.deleted_at.is_(None),
        )
        .first()
    )
    if identification is None:
        raise NotFoundError("Identification")
    return identification


def _check_identification_duplicate(
    db: Session, client_id: int, document_type: str, document_number: str, exclude_id: int | None = None
) -> None:
    number_normalised = document_number.strip().lower()
    for existing in list_identifications(db, client_id):
        if exclude_id is not None and existing.id == exclude_id:
            continue
        if existing.document_type == document_type and existing.document_number.strip().lower() == number_normalised:
            raise ValidationAppError(
                f"A {document_type} with number {document_number} is already on file for this client."
            )


def create_identification(db: Session, client_id: int, payload, user_id: int | None = None) -> ClientIdentification:
    _lock_client(db, client_id)
    _check_identification_duplicate(db, client_id, payload.documentType, payload.documentNumber)

    identification = ClientIdentification(
        client_id=client_id,
        document_type=payload.documentType,
        document_number=payload.documentNumber,
        issue_date=payload.issueDate,
        expiry_date=payload.expiryDate,
        issuing_country=payload.issuingCountry,
    )
    db.add(identification)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Identification added", user_id,
        new_value=f"{identification.document_type}: {identification.document_number}",
    )
    # The client's identification is what project_service._assert_stage_
    # exit_criteria requires before any of THIS client's projects can
    # leave "Enquiry" -- a client can have several projects at once, and
    # this one identification record can be exactly what unblocks all
    # of them, not just whichever project happened to prompt it. Local
    # import: project_service already imports this module at module
    # level, so importing it back at module level here would be
    # circular (same pattern as payment_service._try_auto_advance_
    # project_stage).
    from app.services import project_service

    for project in db.query(Project).filter(Project.client_id == client_id, Project.current_stage == "Enquiry").all():
        project_service.try_auto_advance_stage(db, project, user_id)

    db.commit()
    db.refresh(identification)
    return identification


def update_identification(
    db: Session, client_id: int, identification_id: int, payload, user_id: int | None
) -> ClientIdentification:
    _lock_client(db, client_id)
    identification = get_identification(db, client_id, identification_id)

    new_type = payload.documentType if payload.documentType is not None else identification.document_type
    new_number = payload.documentNumber if payload.documentNumber is not None else identification.document_number
    if payload.documentType is not None or payload.documentNumber is not None:
        _check_identification_duplicate(db, client_id, new_type, new_number, exclude_id=identification_id)

    new_issue = payload.issueDate if payload.issueDate is not None else identification.issue_date
    new_expiry = payload.expiryDate if payload.expiryDate is not None else identification.expiry_date
    if new_expiry <= new_issue:
        raise ValidationAppError("expiryDate must be after issueDate")

    field_map = {
        "documentType": "document_type",
        "documentNumber": "document_number",
        "issueDate": "issue_date",
        "expiryDate": "expiry_date",
        "issuingCountry": "issuing_country",
    }
    changes: dict[str, tuple] = {}
    for api_field, attr in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(identification, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(identification, attr, value)

    audit_service.log_field_changes(
        db, ENTITY_TYPE, client_id, changes, user_id, label_prefix="Updated identification"
    )
    db.commit()
    db.refresh(identification)
    return identification


def delete_identification(db: Session, client_id: int, identification_id: int, user_id: int | None) -> None:
    identification = get_identification(db, client_id, identification_id)
    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Identification removed", user_id,
        previous_value=f"{identification.document_type}: {identification.document_number}",
    )
    identification.deleted_at = datetime.now(timezone.utc)
    db.commit()


def list_consents(db: Session, client_id: int) -> list[ClientConsent]:
    return (
        db.query(ClientConsent)
        .filter(ClientConsent.client_id == client_id)
        .order_by(ClientConsent.id.asc())
        .all()
    )


def create_consent(db: Session, client_id: int, payload, recorded_by: int) -> ClientConsent:
    client = get_client(db, client_id)
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
    db.flush()

    # "Electronic Communication" consent is the single formal, audited
    # decision that covers all three channels (its own description says
    # so: "Allow communication by email, WhatsApp and SMS"). The client
    # row's email_consent/whatsapp_consent/sms_consent flags exist so
    # other features can cheaply check "can we message this client" --
    # this is the one place that keeps them equal to the real decision,
    # rather than leaving them permanently stuck at their creation-time
    # default with no connection to consent actually being granted or
    # withdrawn.
    if payload.consentType == "Electronic Communication":
        client.email_consent = payload.granted
        client.whatsapp_consent = payload.granted
        client.sms_consent = payload.granted

    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Consent recorded", recorded_by,
        new_value=f"{payload.consentType}: {'Granted' if payload.granted else 'Declined'}",
    )
    db.commit()
    db.refresh(consent)
    return consent


def list_documents(db: Session, client_id: int) -> list[ClientDocument]:
    return (
        db.query(ClientDocument)
        .filter(ClientDocument.client_id == client_id, ClientDocument.deleted_at.is_(None))
        .order_by(ClientDocument.id.desc())
        .all()
    )


def create_document(
    db: Session,
    client_id: int,
    category: str,
    title: str,
    issue_date: str | None,
    expiry_date: str | None,
    issuing_authority: str | None,
    file: UploadFile,
    uploaded_by: int,
) -> ClientDocument:
    get_client(db, client_id)

    if category not in CLIENT_DOCUMENT_CATEGORIES:
        raise ValidationAppError(f"category must be one of {CLIENT_DOCUMENT_CATEGORIES}")
    title = title.strip()
    if not title:
        raise ValidationAppError("Document title is required.")

    parsed_issue_date = _parse_optional_date(issue_date, "issueDate")
    parsed_expiry_date = _parse_optional_date(expiry_date, "expiryDate")
    if parsed_issue_date and parsed_expiry_date and parsed_expiry_date <= parsed_issue_date:
        raise ValidationAppError("expiryDate must be after issueDate.")

    storage_key, original_filename, size_bytes = save_upload(file, "client_documents")

    document = ClientDocument(
        client_id=client_id,
        category=category,
        title=title,
        issue_date=parsed_issue_date,
        expiry_date=parsed_expiry_date,
        issuing_authority=issuing_authority.strip() if issuing_authority else None,
        version=1,
        verification_status="Pending",
        uploaded_by=uploaded_by,
        upload_date=datetime.now(timezone.utc),
        storage_key=storage_key,
        original_filename=original_filename,
        file_size_bytes=size_bytes,
    )
    db.add(document)
    db.flush()

    # Same fix as project documents (document_service.create_document):
    # record the initial upload as a real version immediately, rather
    # than only ever having version history if the file is later
    # replaced.
    db.add(
        ClientDocumentVersion(
            document_id=document.id,
            version=1,
            uploaded_by=uploaded_by,
            upload_date=document.upload_date,
            notes="Initial upload.",
            storage_key=storage_key,
            original_filename=original_filename,
            file_size_bytes=size_bytes,
        )
    )

    audit_service.log_event(db, ENTITY_TYPE, client_id, "Document uploaded", uploaded_by, new_value=document.title)
    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, client_id: int, document_id: int) -> ClientDocument:
    document = (
        db.query(ClientDocument)
        .filter(
            ClientDocument.id == document_id,
            ClientDocument.client_id == client_id,
            ClientDocument.deleted_at.is_(None),
        )
        .first()
    )
    if document is None:
        raise NotFoundError("Client document")
    return document


def update_document(db: Session, client_id: int, document_id: int, payload, user_id: int | None) -> ClientDocument:
    document = get_document(db, client_id, document_id)

    new_issue = payload.issueDate if payload.issueDate is not None else document.issue_date
    new_expiry = payload.expiryDate if payload.expiryDate is not None else document.expiry_date
    if new_issue and new_expiry and new_expiry <= new_issue:
        raise ValidationAppError("expiryDate must be after issueDate")

    field_map = {
        "category": "category",
        "title": "title",
        "issueDate": "issue_date",
        "expiryDate": "expiry_date",
        "issuingAuthority": "issuing_authority",
    }
    changes: dict[str, tuple] = {}
    for api_field, attr in field_map.items():
        value = getattr(payload, api_field)
        if value is not None:
            old = getattr(document, attr)
            if old != value:
                changes[attr] = (old, value)
            setattr(document, attr, value)

    audit_service.log_field_changes(db, ENTITY_TYPE, client_id, changes, user_id, label_prefix="Updated document")
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, client_id: int, document_id: int, user_id: int | None) -> None:
    document = get_document(db, client_id, document_id)
    audit_service.log_event(db, ENTITY_TYPE, client_id, "Document removed", user_id, previous_value=document.title)
    document.deleted_at = datetime.now(timezone.utc)
    db.commit()


def replace_document_file(db: Session, client_id: int, document_id: int, file: UploadFile, notes: str | None, user_id: int | None) -> ClientDocument:
    """Uploads a new file for an existing document record, bumping its
    version. Previously this just overwrote storage_key in place with no
    history at all -- the old file was never deleted from disk, but
    there was no way to ever see or recover it again through the app.
    Now mirrors the same real version-history approach project documents
    use (document_service.add_version): the old file's own version row
    was already created either when the document was first uploaded or
    by a previous replace, so this only needs to add the new one."""
    document = get_document(db, client_id, document_id)
    storage_key, original_filename, size_bytes = save_upload(file, "client_documents")

    document.storage_key = storage_key
    document.original_filename = original_filename
    document.file_size_bytes = size_bytes
    document.version += 1
    document.verification_status = "Pending"  # a replaced file needs re-verifying, not inheriting the old one's status

    db.add(
        ClientDocumentVersion(
            document_id=document.id,
            version=document.version,
            uploaded_by=user_id,
            upload_date=datetime.now(timezone.utc),
            notes=notes.strip() if notes and notes.strip() else f"Replaced with version {document.version}.",
            storage_key=storage_key,
            original_filename=original_filename,
            file_size_bytes=size_bytes,
        )
    )

    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Document file replaced", user_id,
        new_value=f"{document.title} (v{document.version})",
    )
    db.commit()
    db.refresh(document)
    return document


def get_document_versions(db: Session, client_id: int, document_id: int) -> list[ClientDocumentVersion]:
    document = get_document(db, client_id, document_id)
    return (
        db.query(ClientDocumentVersion)
        .filter(ClientDocumentVersion.document_id == document.id)
        .order_by(ClientDocumentVersion.id.asc())
        .all()
    )


def get_document_version_download_target(db: Session, client_id: int, document_id: int, version_id: int) -> tuple:
    document = get_document(db, client_id, document_id)
    version = (
        db.query(ClientDocumentVersion)
        .filter(ClientDocumentVersion.id == version_id, ClientDocumentVersion.document_id == document.id)
        .first()
    )
    if version is None:
        raise NotFoundError("Version")
    if not version.storage_key:
        raise ValidationAppError("This version has no file on record.")
    return resolve_path(version.storage_key), version.original_filename


def get_document_download_target(db: Session, client_id: int, document_id: int) -> tuple:
    document = get_document(db, client_id, document_id)
    if not document.storage_key:
        # Legacy row from before file storage was fixed (or demo seed
        # data) -- there's genuinely no file behind it, so fail clearly
        # rather than trying to resolve an empty path.
        raise ValidationAppError("This document has no file on record (it predates file uploads being enabled).")
    return resolve_path(document.storage_key), document.original_filename


def list_verifications(db: Session, client_id: int) -> list[ClientVerification]:
    # A verification tied to a specific document (document_id is set)
    # stops counting once that document is deleted -- otherwise a
    # "Rejected"/"Pending" verification for a document that's since been
    # removed (e.g. the wrong file, replaced by a corrected upload) would
    # keep silently blocking calculateOnboardingState()'s suggested next
    # state on the frontend even though there's nothing left to act on.
    # Checklist-style verifications (document_id is null) are unaffected.
    return (
        db.query(ClientVerification)
        .outerjoin(ClientDocument, ClientVerification.document_id == ClientDocument.id)
        .filter(
            ClientVerification.client_id == client_id,
            or_(ClientVerification.document_id.is_(None), ClientDocument.deleted_at.is_(None)),
        )
        .order_by(ClientVerification.id.desc())
        .all()
    )


def create_verification(
    db: Session,
    client_id: int,
    item: str,
    result: str,
    notes: str | None,
    document_id_raw: str | None,
    verified_by: int,
) -> ClientVerification:
    get_client(db, client_id)

    if result not in CLIENT_VERIFICATION_RESULTS:
        raise ValidationAppError(f"result must be one of {CLIENT_VERIFICATION_RESULTS}")
    item = item.strip()
    if not item:
        raise ValidationAppError("item is required.")

    document: ClientDocument | None = None
    if document_id_raw:
        document = get_document(db, client_id, parse_document_id(document_id_raw))

    verification = ClientVerification(
        client_id=client_id,
        document_id=document.id if document else None,
        item=item,
        result=result,
        verified_by=verified_by,
        verified_date=datetime.now(timezone.utc),
        notes=notes.strip() if notes else None,
    )
    db.add(verification)
    db.flush()

    # A verification tied to a specific document is the authoritative
    # source for that document's own status -- keep them in sync instead
    # of leaving the document stuck on "Pending" forever.
    if document is not None:
        document.verification_status = result

    audit_service.log_event(
        db, ENTITY_TYPE, client_id, "Verification recorded", verified_by,
        new_value=f"{item}: {result}",
    )
    db.commit()
    db.refresh(verification)
    return verification


def delete_client(db: Session, client_id: int, actor_id: int) -> None:
    client = get_client(db, client_id)

    # Soft-deleting a client is an app-level flag, not a real row delete,
    # so the FK's ON DELETE RESTRICT on projects.client_id never fires --
    # without this check a client with live projects could be "deleted"
    # while those projects silently keep pointing at it.
    from app.models.project import Project  # local import: avoids a circular import at module load time

    active_projects = (
        db.query(Project).filter(Project.client_id == client_id, Project.deleted_at.is_(None)).count()
    )
    if active_projects > 0:
        raise ValidationAppError(
            f"This client has {active_projects} project(s) on file and cannot be deleted. "
            "Close or reassign those projects first."
        )

    audit_service.log_event(db, ENTITY_TYPE, client.id, "Client deleted", actor_id, previous_value=client.company_name)
    client.deleted_at = datetime.now(timezone.utc)
    db.commit()
