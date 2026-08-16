from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.file_storage import format_file_size
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.client import (
    ClientAddressCreate,
    ClientAddressOut,
    ClientAddressUpdate,
    ClientConsentCreate,
    ClientConsentOut,
    ClientContactCreate,
    ClientContactOut,
    ClientContactUpdate,
    ClientCreate,
    ClientDocumentOut,
    ClientDocumentUpdate,
    ClientDuplicateMatchOut,
    ClientIdentificationCreate,
    ClientIdentificationOut,
    ClientIdentificationUpdate,
    ClientOnboardingStateUpdate,
    ClientOut,
    ClientStatusUpdate,
    ClientUpdate,
    ClientVerificationCreate,
    ClientVerificationOut,
)
from app.services import client_service

router = APIRouter(prefix="/api/clients", tags=["clients"])

can_view = require_permission("Clients", "view")
can_edit = require_permission("Clients", "edit")
can_delete = require_permission("Clients", "delete")


@router.get("", response_model=PagedResponse[ClientOut])
def list_clients(
    search: str | None = None,
    clientType: str | None = None,
    status: str | None = None,
    onboardingState: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    result = client_service.list_clients(
        db, search, clientType, status, onboardingState, sort, page, pageSize
    )
    result["items"] = [ClientOut.from_model(c) for c in result["items"]]
    return result


@router.post("/duplicates", response_model=list[ClientDuplicateMatchOut])
def find_duplicates(name: str, mobile: str, email: str, db: Session = Depends(get_db), _=Depends(can_view)):
    matches = client_service.find_possible_duplicates(db, name, mobile, email)
    return [
        ClientDuplicateMatchOut(client=ClientOut.from_model(m["client"]), matchedOn=m["matchedOn"])
        for m in matches
    ]


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    client = client_service.get_client(db, client_service.parse_client_id(client_id))
    return ClientOut.from_model(client)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.create_client(db, payload, current_user.id)
    return ClientOut.from_model(client)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: str,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.update_client(
        db, client_service.parse_client_id(client_id), payload, current_user.id
    )
    return ClientOut.from_model(client)


@router.patch("/{client_id}/status", response_model=ClientOut)
def set_client_status(
    client_id: str,
    payload: ClientStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.set_status(
        db, client_service.parse_client_id(client_id), payload.status, current_user.id
    )
    return ClientOut.from_model(client)


@router.patch("/{client_id}/onboarding-state", response_model=ClientOut)
def set_onboarding_state(
    client_id: str,
    payload: ClientOnboardingStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.set_onboarding_state(
        db,
        client_service.parse_client_id(client_id),
        payload.onboardingState,
        payload.reason,
        current_user.id,
    )
    return ClientOut.from_model(client)


@router.get("/{client_id}/contacts", response_model=list[ClientContactOut])
def list_contacts(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    contacts = client_service.list_contacts(db, client_service.parse_client_id(client_id))
    return [ClientContactOut.from_model(c) for c in contacts]


@router.post("/{client_id}/contacts", response_model=ClientContactOut, status_code=201)
def create_contact(
    client_id: str, payload: ClientContactCreate, db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contact = client_service.create_contact(db, client_service.parse_client_id(client_id), payload, current_user.id)
    return ClientContactOut.from_model(contact)


@router.patch("/{client_id}/contacts/{contact_id}", response_model=ClientContactOut)
def update_contact(
    client_id: str, contact_id: str, payload: ClientContactUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contact = client_service.update_contact(
        db, client_service.parse_client_id(client_id), client_service.parse_prefixed_id(contact_id, "CTC-", "contact"), payload, current_user.id
    )
    return ClientContactOut.from_model(contact)


@router.delete("/{client_id}/contacts/{contact_id}", status_code=204)
def delete_contact(
    client_id: str, contact_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    client_service.delete_contact(
        db, client_service.parse_client_id(client_id), client_service.parse_prefixed_id(contact_id, "CTC-", "contact"), current_user.id
    )


@router.get("/{client_id}/addresses", response_model=list[ClientAddressOut])
def list_addresses(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    addresses = client_service.list_addresses(db, client_service.parse_client_id(client_id))
    return [ClientAddressOut.from_model(a) for a in addresses]


@router.post("/{client_id}/addresses", response_model=ClientAddressOut, status_code=201)
def create_address(
    client_id: str, payload: ClientAddressCreate, db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    address = client_service.create_address(db, client_service.parse_client_id(client_id), payload, current_user.id)
    return ClientAddressOut.from_model(address)


@router.patch("/{client_id}/addresses/{address_id}", response_model=ClientAddressOut)
def update_address(
    client_id: str, address_id: str, payload: ClientAddressUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    address = client_service.update_address(
        db, client_service.parse_client_id(client_id), client_service.parse_prefixed_id(address_id, "ADR-", "address"), payload, current_user.id
    )
    return ClientAddressOut.from_model(address)


@router.delete("/{client_id}/addresses/{address_id}", status_code=204)
def delete_address(
    client_id: str, address_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    client_service.delete_address(
        db, client_service.parse_client_id(client_id), client_service.parse_prefixed_id(address_id, "ADR-", "address"), current_user.id
    )


@router.get("/{client_id}/identifications", response_model=list[ClientIdentificationOut])
def list_identifications(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    identifications = client_service.list_identifications(db, client_service.parse_client_id(client_id))
    return [ClientIdentificationOut.from_model(i) for i in identifications]


@router.post("/{client_id}/identifications", response_model=ClientIdentificationOut, status_code=201)
def create_identification(
    client_id: str,
    payload: ClientIdentificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    identification = client_service.create_identification(
        db, client_service.parse_client_id(client_id), payload, current_user.id
    )
    return ClientIdentificationOut.from_model(identification)


@router.patch("/{client_id}/identifications/{identification_id}", response_model=ClientIdentificationOut)
def update_identification(
    client_id: str,
    identification_id: str,
    payload: ClientIdentificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    identification = client_service.update_identification(
        db,
        client_service.parse_client_id(client_id),
        client_service.parse_prefixed_id(identification_id, "IDN-", "identification"),
        payload,
        current_user.id,
    )
    return ClientIdentificationOut.from_model(identification)


@router.delete("/{client_id}/identifications/{identification_id}", status_code=204)
def delete_identification(
    client_id: str, identification_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    client_service.delete_identification(
        db,
        client_service.parse_client_id(client_id),
        client_service.parse_prefixed_id(identification_id, "IDN-", "identification"),
        current_user.id,
    )


@router.get("/{client_id}/consents", response_model=list[ClientConsentOut])
def list_consents(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    consents = client_service.list_consents(db, client_service.parse_client_id(client_id))
    names = {u.id: u.full_name for u in db.query(User).filter(
        User.id.in_({c.recorded_by for c in consents})
    ).all()} if consents else {}
    return [ClientConsentOut.from_model(c, names.get(c.recorded_by, "Unknown")) for c in consents]


@router.post("/{client_id}/consents", response_model=ClientConsentOut, status_code=201)
def create_consent(
    client_id: str,
    payload: ClientConsentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    consent = client_service.create_consent(
        db, client_service.parse_client_id(client_id), payload, current_user.id
    )
    return ClientConsentOut.from_model(consent, current_user.full_name)


@router.get("/{client_id}/audit-events")
def list_audit_events(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return client_service.get_audit_events(db, client_service.parse_client_id(client_id))


@router.get("/{client_id}/documents", response_model=list[ClientDocumentOut])
def list_documents(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    documents = client_service.list_documents(db, client_service.parse_client_id(client_id))
    names = {u.id: u.full_name for u in db.query(User).filter(
        User.id.in_({d.uploaded_by for d in documents})
    ).all()} if documents else {}
    return [
        ClientDocumentOut.from_model(d, names.get(d.uploaded_by, "Unknown"), format_file_size(d.file_size_bytes))
        for d in documents
    ]


@router.post("/{client_id}/documents", response_model=ClientDocumentOut, status_code=201)
def create_document(
    client_id: str,
    category: str = Form(...),
    title: str = Form(...),
    issueDate: str | None = Form(default=None),
    expiryDate: str | None = Form(default=None),
    issuingAuthority: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = client_service.create_document(
        db,
        client_service.parse_client_id(client_id),
        category,
        title,
        issueDate,
        expiryDate,
        issuingAuthority,
        file,
        current_user.id,
    )
    return ClientDocumentOut.from_model(document, current_user.full_name, format_file_size(document.file_size_bytes))


@router.get("/{client_id}/documents/{document_id}/download")
def download_document(
    client_id: str, document_id: str, db: Session = Depends(get_db), _=Depends(can_view)
):
    path, original_filename = client_service.get_document_download_target(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id)
    )
    return FileResponse(path, filename=original_filename)


@router.patch("/{client_id}/documents/{document_id}", response_model=ClientDocumentOut)
def update_document(
    client_id: str,
    document_id: str,
    payload: ClientDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = client_service.update_document(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id), payload, current_user.id
    )
    uploader = db.query(User).filter(User.id == document.uploaded_by).first()
    uploader_name = uploader.full_name if uploader else "Unknown"
    return ClientDocumentOut.from_model(document, uploader_name, format_file_size(document.file_size_bytes))


@router.delete("/{client_id}/documents/{document_id}", status_code=204)
def delete_document(
    client_id: str, document_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    client_service.delete_document(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id), current_user.id
    )


@router.get("/{client_id}/verifications", response_model=list[ClientVerificationOut])
def list_verifications(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    verifications = client_service.list_verifications(db, client_service.parse_client_id(client_id))
    names = {u.id: u.full_name for u in db.query(User).filter(
        User.id.in_({v.verified_by for v in verifications})
    ).all()} if verifications else {}
    return [
        ClientVerificationOut.from_model(v, names.get(v.verified_by, "Unknown")) for v in verifications
    ]


@router.post("/{client_id}/verifications", response_model=ClientVerificationOut, status_code=201)
def create_verification(
    client_id: str,
    payload: ClientVerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    verification = client_service.create_verification(
        db,
        client_service.parse_client_id(client_id),
        payload.item,
        payload.result,
        payload.notes,
        payload.documentId,
        current_user.id,
    )
    return ClientVerificationOut.from_model(verification, current_user.full_name)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    client_service.delete_client(db, client_service.parse_client_id(client_id), current_user.id)
