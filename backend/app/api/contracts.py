from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.schemas.contract import (
    ContractCreate,
    ContractOut,
    ContractRevisionCreate,
    ContractStatusUpdate,
    ContractUpdate,
)
from app.schemas.document_template import DocumentEmailRequest
from app.services import contract_service, document_template_service, email_service

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, contract) -> ContractOut:
    from app.models.quotation import Quotation

    project = db.query(Project).filter(Project.id == contract.project_id).first()
    prepared_by_name = _user_name(db, contract.prepared_by)
    clauses = contract_service.get_clauses(db, contract.id)
    revisions = contract_service.get_revisions_with_names(db, contract.id)
    quotation_no = None
    if contract.quotation_id is not None:
        quotation = db.query(Quotation).filter(Quotation.id == contract.quotation_id).first()
        quotation_no = quotation.quotation_no if quotation else None
    return ContractOut.from_model(
        contract, project.project_no if project else "", prepared_by_name, clauses, revisions, quotation_no
    )


@router.get("", response_model=list[ContractOut])
def list_contracts(
    projectId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    return [_to_out(db, c) for c in contract_service.list_contracts(db, projectId, status)]


@router.get("/{contract_no}", response_model=ContractOut)
def get_contract(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, contract_service.get_contract(db, contract_no))


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(
    payload: ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    contract = contract_service.create_contract(db, payload, current_user.id)
    return _to_out(db, contract)


@router.patch("/{contract_no}", response_model=ContractOut)
def update_contract(
    contract_no: str,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.update_contract(db, contract_no, payload, current_user.id)
    return _to_out(db, contract)


@router.post("/{contract_no}/finalize", response_model=ContractOut)
def finalize_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    contract = contract_service.finalize_contract(db, contract_no, current_user.id)
    return _to_out(db, contract)


@router.post("/{contract_no}/reopen", response_model=ContractOut)
def reopen_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    contract = contract_service.reopen_contract(db, contract_no, current_user.id)
    return _to_out(db, contract)


@router.patch("/{contract_no}/status", response_model=ContractOut)
def set_status(
    contract_no: str,
    payload: ContractStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.set_status(
        db, contract_no, payload.status, payload.reason, current_user.id
    )
    return _to_out(db, contract)


@router.post("/{contract_no}/revisions", response_model=ContractOut, status_code=201)
def add_revision(
    contract_no: str,
    payload: ContractRevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    contract = contract_service.add_revision(db, contract_no, payload.summary, current_user.id)
    return _to_out(db, contract)


@router.get("/{contract_no}/document")
def download_document(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    contract = contract_service.get_contract(db, contract_no)
    content, filename = document_template_service.render_contract_document(db, contract)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{contract_no}/document/pdf")
def download_document_pdf(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    contract = contract_service.get_contract(db, contract_no)
    content, filename = document_template_service.render_contract_pdf(db, contract)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/{contract_no}/document/email", status_code=204)
def email_document(
    contract_no: str,
    payload: DocumentEmailRequest,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    contract = contract_service.get_contract(db, contract_no)
    project = db.query(Project).filter(Project.id == contract.project_id).first()
    client = db.query(Client).filter(Client.id == project.client_id).first() if project else None
    to_email = payload.toEmail or (client.email if client else None)
    if not to_email:
        raise ValidationAppError("No recipient email address on file for this project's client.")

    content, filename = document_template_service.render_contract_pdf(db, contract)
    email_service.send_document_email(
        to_email=to_email,
        subject=f"Contract {contract.contract_no}",
        body_text=f"Please find attached Contract {contract.contract_no}.",
        attachment_bytes=content,
        attachment_filename=filename,
        attachment_mimetype="application/pdf",
    )


@router.get("/{contract_no}/audit-events")
def list_audit_events(contract_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return contract_service.get_audit_events(db, contract_no)


@router.delete("/{contract_no}", status_code=204)
def delete_contract(contract_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    contract_service.delete_contract(db, contract_no, current_user.id)


