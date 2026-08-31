from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.core.file_storage import resolve_path
from app.models.user import User
from app.schemas.document_template import DocumentTemplateOut
from app.services import document_template_service

router = APIRouter(prefix="/api/document-templates", tags=["document-templates"])

can_view = require_permission("Documents", "view")
can_edit = require_permission("Documents", "edit")
can_delete = require_permission("Documents", "delete")


def _parse_id(raw: str) -> int:
    text = raw.removeprefix("TPL-") if raw.upper().startswith("TPL-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid document template id.")
    return int(text)


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _to_out(db: Session, template) -> DocumentTemplateOut:
    return DocumentTemplateOut.from_model(template, _user_name(db, template.uploaded_by))


@router.get("", response_model=list[DocumentTemplateOut])
def list_templates(documentType: str | None = None, db: Session = Depends(get_db), _=Depends(can_view)):
    return [_to_out(db, t) for t in document_template_service.list_templates(db, documentType)]


@router.post("", response_model=DocumentTemplateOut, status_code=201)
def upload_template(
    documentType: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    template = document_template_service.upload_template(db, documentType, file, current_user.id)
    return _to_out(db, template)


@router.patch("/{template_id}/default", response_model=DocumentTemplateOut)
def set_default(template_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    template = document_template_service.set_default(db, _parse_id(template_id), current_user.id)
    return _to_out(db, template)


@router.get("/{template_id}/download")
def download_template(template_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    template = document_template_service.get_template(db, _parse_id(template_id))
    content = resolve_path(template.storage_key).read_bytes()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{template.original_filename}"'},
    )


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_delete)):
    document_template_service.delete_template(db, _parse_id(template_id), current_user.id)
