import base64
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.core.file_storage import format_file_size, matches_signature
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
    ClientDocumentVersionOut,
    IdentificationVerificationOut,
    ClientDocumentUpdate,
    ClientDuplicateCheckRequest,
    ClientDuplicateMatchOut,
    ClientIdentificationCreate,
    ClientIdentificationOut,
    ClientIdentificationUpdate,
    ClientMergeRequest,
    ClientOnboardingStateUpdate,
    ClientOut,
    ClientStatusUpdate,
    ClientUpdate,
    ClientVerificationCreate,
    ClientVerificationOut,
)
from app.services import ai_service, client_service

router = APIRouter(prefix="/api/clients", tags=["clients"])

can_view = require_permission("Clients", "view")
can_edit = require_permission("Clients", "edit")
can_delete = require_permission("Clients", "delete")


def _account_manager_names(db: Session, clients: list) -> dict[int, str]:
    ids = {c.account_manager_id for c in clients if c.account_manager_id}
    if not ids:
        return {}
    return {u.id: u.full_name for u in db.query(User).filter(User.id.in_(ids)).all()}


def _client_out(client, names: dict[int, str]) -> ClientOut:
    return ClientOut.from_model(client, names.get(client.account_manager_id))


@router.get("", response_model=PagedResponse[ClientOut])
def list_clients(
    search: str | None = None,
    clientType: str | None = None,
    status: str | None = None,
    onboardingState: str | None = None,
    accountManagerId: str | None = None,
    sort: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    result = client_service.list_clients(
        db, search, clientType, status, onboardingState, accountManagerId, sort, page, pageSize
    )
    names = _account_manager_names(db, result["items"])
    result["items"] = [_client_out(c, names) for c in result["items"]]
    return result


@router.post("/duplicates", response_model=list[ClientDuplicateMatchOut])
def find_duplicates(payload: ClientDuplicateCheckRequest, db: Session = Depends(get_db), _=Depends(can_view)):
    matches = client_service.find_possible_duplicates(
        db, payload.name, payload.mobile, payload.email, payload.registrationNumber
    )
    names = _account_manager_names(db, [m["client"] for m in matches])
    return [
        ClientDuplicateMatchOut(client=_client_out(m["client"], names), matchedOn=m["matchedOn"])
        for m in matches
    ]


@router.get("/{client_id}/duplicate-identifications", response_model=list[ClientDuplicateMatchOut])
def find_identification_duplicates(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    matches = client_service.find_clients_with_matching_identification(
        db, client_service.parse_client_id(client_id)
    )
    names = _account_manager_names(db, [m["client"] for m in matches])
    return [
        ClientDuplicateMatchOut(client=_client_out(m["client"], names), matchedOn=m["matchedOn"])
        for m in matches
    ]


@router.post("/{target_client_id}/merge", response_model=ClientOut)
def merge_clients(
    target_client_id: str,
    payload: ClientMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_delete),
):
    merged = client_service.merge_clients(
        db,
        client_service.parse_client_id(payload.sourceClientId),
        client_service.parse_client_id(target_client_id),
        current_user.id,
    )
    names = _account_manager_names(db, [merged])
    return _client_out(merged, names)


# Constraints specific to the identification-document upload in the New
# Client wizard -- deliberately not the general document-upload limits
# used elsewhere (backend/app/core/file_storage.py's ALLOWED_EXTENSIONS/
# MAX_UPLOAD_SIZE_MB), since those need to stay permissive for other
# client and project document types.
IDENTIFICATION_MAX_SIZE_MB = 5
IDENTIFICATION_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
IDENTIFICATION_IMAGE_MIME_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


@router.post("/verify-identification-document", response_model=IdentificationVerificationOut)
async def verify_identification_document(
    file: UploadFile = File(...),
    documentType: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    """Not scoped to a client id -- called from the New Client wizard
    before any client record exists yet. Size/type are hard limits,
    enforced regardless of AI availability (a 6 MB file or a .docx
    doesn't become acceptable just because the AI check can't run).
    The AI plausibility check itself degrades gracefully: PDFs (Claude
    vision here only takes images) and any AI failure both return
    checked=false rather than an error, which the frontend accepts the
    file for, flagged for manual verification -- per @app.core.
    exceptions.AppError's own convention, ai_service.AIUnavailableError
    is the only path this ever raises AS an error to the client.
    """
    extension = Path(file.filename or "").suffix.lower()
    if extension not in IDENTIFICATION_ALLOWED_EXTENSIONS:
        raise ValidationAppError(
            f"File type '{extension or 'unknown'}' is not allowed. "
            f"Allowed types: {', '.join(sorted(IDENTIFICATION_ALLOWED_EXTENSIONS))}"
        )

    max_bytes = IDENTIFICATION_MAX_SIZE_MB * 1024 * 1024
    contents = await file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise ValidationAppError(f"File exceeds the {IDENTIFICATION_MAX_SIZE_MB} MB upload limit.")
    if not contents:
        raise ValidationAppError("Uploaded file is empty.")
    if not matches_signature(extension, contents):
        raise ValidationAppError(f"File content doesn't match its '{extension}' extension.")

    if extension not in IDENTIFICATION_IMAGE_MIME_TYPES:
        # PDF -- outside what this check can look at; accept with the caveat.
        return IdentificationVerificationOut(checked=False)

    try:
        result = await ai_service.verify_identification_document(
            db, base64.b64encode(contents).decode("ascii"), IDENTIFICATION_IMAGE_MIME_TYPES[extension], documentType
        )
        return IdentificationVerificationOut(checked=True, matches=result["matches"], reasoning=result["reasoning"])
    except ai_service.AIUnavailableError:
        return IdentificationVerificationOut(checked=False)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    client = client_service.get_client(db, client_service.parse_client_id(client_id))
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.create_client(db, payload, current_user.id)
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


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
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


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
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


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
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


@router.post("/{client_id}/onboarding-state/auto-advance", response_model=ClientOut)
def auto_advance_onboarding(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    client = client_service.auto_advance_onboarding(
        db, client_service.parse_client_id(client_id), current_user.id
    )
    names = _account_manager_names(db, [client])
    return _client_out(client, names)


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


@router.post("/{client_id}/documents/{document_id}/replace-file", response_model=ClientDocumentOut)
def replace_document_file(
    client_id: str,
    document_id: str,
    file: UploadFile = File(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    document = client_service.replace_document_file(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id), file, notes, current_user.id
    )
    uploader = db.query(User).filter(User.id == document.uploaded_by).first()
    uploader_name = uploader.full_name if uploader else "Unknown"
    return ClientDocumentOut.from_model(document, uploader_name, format_file_size(document.file_size_bytes))


@router.get("/{client_id}/documents/{document_id}/versions", response_model=list[ClientDocumentVersionOut])
def list_document_versions(client_id: str, document_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    versions = client_service.get_document_versions(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id)
    )
    names = {u.id: u.full_name for u in db.query(User).filter(
        User.id.in_({v.uploaded_by for v in versions})
    ).all()} if versions else {}
    return [
        ClientDocumentVersionOut.from_model(v, names.get(v.uploaded_by, "Unknown"))
        for v in versions
    ]


@router.get("/{client_id}/documents/{document_id}/versions/{version_id}/download")
def download_document_version(
    client_id: str, document_id: str, version_id: int, db: Session = Depends(get_db), _=Depends(can_view)
):
    path, original_filename = client_service.get_document_version_download_target(
        db, client_service.parse_client_id(client_id), client_service.parse_document_id(document_id), version_id
    )
    return FileResponse(path, filename=original_filename)


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
