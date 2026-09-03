from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.schemas.document_template import DocumentEmailRequest
from app.schemas.quotation import (
    QuotationCreate,
    QuotationOut,
    QuotationStatusUpdate,
    QuotationUpdate,
)
from app.services import document_template_service, email_service, quotation_service

router = APIRouter(prefix="/api/quotations", tags=["quotations"])

can_view = require_permission("Projects", "view")
can_edit = require_permission("Projects", "edit")
can_delete = require_permission("Projects", "delete")


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, quotation) -> QuotationOut:
    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    prepared_by_name = _user_name(db, quotation.prepared_by)
    line_items = quotation_service.get_line_items(db, quotation.id)
    revisions = quotation_service.get_revisions_with_names(db, quotation.id)
    return QuotationOut.from_model(
        quotation, project.project_no if project else "", prepared_by_name, line_items, revisions
    )


@router.get("", response_model=list[QuotationOut])
def list_quotations(
    projectId: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    return [_to_out(db, q) for q in quotation_service.list_quotations(db, projectId, status)]


@router.get("/{quotation_no}", response_model=QuotationOut)
def get_quotation(quotation_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return _to_out(db, quotation_service.get_quotation(db, quotation_no))


@router.post("", response_model=QuotationOut, status_code=201)
def create_quotation(
    payload: QuotationCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit)
):
    quotation = quotation_service.create_quotation(db, payload, current_user.id)
    return _to_out(db, quotation)


@router.patch("/{quotation_no}", response_model=QuotationOut)
def update_quotation(
    quotation_no: str,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    quotation = quotation_service.update_quotation(db, quotation_no, payload, current_user.id)
    return _to_out(db, quotation)


@router.post("/{quotation_no}/finalize", response_model=QuotationOut)
def finalize_quotation(quotation_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    quotation = quotation_service.finalize_quotation(db, quotation_no, current_user.id)
    return _to_out(db, quotation)


@router.post("/{quotation_no}/reopen", response_model=QuotationOut)
def reopen_quotation(quotation_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    quotation = quotation_service.reopen_quotation(db, quotation_no, current_user.id)
    return _to_out(db, quotation)


@router.patch("/{quotation_no}/status", response_model=QuotationOut)
def set_status(
    quotation_no: str,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    quotation = quotation_service.set_status(
        db, quotation_no, payload.status, payload.reason, current_user.id
    )
    return _to_out(db, quotation)


@router.get("/{quotation_no}/document")
def download_document(quotation_no: str, language: str | None = None, db: Session = Depends(get_db), _=Depends(can_view)):
    quotation = quotation_service.get_quotation(db, quotation_no)
    content, filename = document_template_service.render_quotation_document(db, quotation, language)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{quotation_no}/document/pdf")
def download_document_pdf(quotation_no: str, language: str | None = None, db: Session = Depends(get_db), _=Depends(can_view)):
    quotation = quotation_service.get_quotation(db, quotation_no)
    content, filename = document_template_service.render_quotation_pdf(db, quotation, language)
    return Response(
        content=content,
        media_type="application/pdf",
        # inline, not attachment -- this is what Print opens in a new tab
        # to send straight to the browser's PDF viewer/print dialog.
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/{quotation_no}/document/email", status_code=204)
def email_document(
    quotation_no: str,
    payload: DocumentEmailRequest,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    quotation = quotation_service.get_quotation(db, quotation_no)
    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    client = db.query(Client).filter(Client.id == project.client_id).first() if project else None
    to_email = payload.toEmail or (client.email if client else None)
    if not to_email:
        raise ValidationAppError("No recipient email address on file for this project's client.")

    content, filename = document_template_service.render_quotation_pdf(db, quotation, payload.language)
    email_service.send_document_email(
        to_email=to_email,
        subject=f"Quotation {quotation.quotation_no}",
        body_text=f"Please find attached Quotation {quotation.quotation_no}.",
        attachment_bytes=content,
        attachment_filename=filename,
        attachment_mimetype="application/pdf",
    )


@router.get("/{quotation_no}/audit-events")
def list_audit_events(quotation_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return quotation_service.get_audit_events(db, quotation_no)


@router.delete("/{quotation_no}", status_code=204)
def delete_quotation(quotation_no: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    quotation_service.delete_quotation(db, quotation_no, current_user.id)
