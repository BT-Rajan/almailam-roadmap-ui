"""Admin-uploaded .docx templates for Quotation/Contract documents.

An Administrator uploads a .docx per document_type (Quotation, Contract)
under Administration > Documents and marks one as the default. When a
project's Quotation/Contract tab asks for the actual document, the
default template's placeholders ({{ field }}, and {%tr for ... %} row
loops inside a table -- both standard docxtpl/Jinja2 syntax) are merged
with that record's live data via render_quotation_document/
render_contract_document below, and the merged .docx is what gets
downloaded. There is no PDF conversion step -- the merged .docx is the
deliverable, opened/printed from Word like any other document.
"""

import html
import io
import re
from datetime import datetime, timezone
from decimal import Decimal

from docxtpl import DocxTemplate
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.models.client import Client
from app.models.contract import Contract
from app.models.document_template import DOCUMENT_TEMPLATE_TYPES, DocumentTemplate
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.user import User
from app.services import audit_service

ENTITY_TYPE = "DOCUMENT_TEMPLATE"
STORAGE_SUBDIRECTORY = "document-templates"

_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_BREAK_RE = re.compile(r"</(p|div|li|br)\s*/?>", re.IGNORECASE)


def _plain_text(value: str | None) -> str:
    """Strips the small rich-text HTML allowlist (see
    core/html_sanitizer.py) down to plain text for a Word merge field --
    a .docx template has no way to render arbitrary saved HTML, only
    plain text/Jinja2 placeholders. Block-level tags become newlines so
    paragraphs/list items don't run together; everything else is
    stripped outright (inline images included -- they don't survive the
    merge, only their surrounding text does)."""
    if not value:
        return ""
    with_breaks = _BLOCK_BREAK_RE.sub("\n", value)
    stripped = _TAG_RE.sub("", with_breaks)
    return html.unescape(stripped).strip()


def _user_name(db: Session, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    return user.full_name if user else "Unknown"


def _check_document_type(document_type: str) -> None:
    if document_type not in DOCUMENT_TEMPLATE_TYPES:
        raise ValidationAppError(f"documentType must be one of {DOCUMENT_TEMPLATE_TYPES}")


def list_templates(db: Session, document_type: str | None = None) -> list[DocumentTemplate]:
    query = db.query(DocumentTemplate).filter(DocumentTemplate.deleted_at.is_(None))
    if document_type is not None:
        _check_document_type(document_type)
        query = query.filter(DocumentTemplate.document_type == document_type)
    return query.order_by(DocumentTemplate.id.desc()).all()


def get_template(db: Session, template_id: int) -> DocumentTemplate:
    template = (
        db.query(DocumentTemplate)
        .filter(DocumentTemplate.id == template_id, DocumentTemplate.deleted_at.is_(None))
        .first()
    )
    if template is None:
        raise NotFoundError("Document template")
    return template


def get_default(db: Session, document_type: str) -> DocumentTemplate | None:
    _check_document_type(document_type)
    return (
        db.query(DocumentTemplate)
        .filter(
            DocumentTemplate.document_type == document_type,
            DocumentTemplate.is_default.is_(True),
            DocumentTemplate.deleted_at.is_(None),
        )
        .first()
    )


def upload_template(db: Session, document_type: str, file, actor_id: int) -> DocumentTemplate:
    _check_document_type(document_type)
    if not (file.filename or "").lower().endswith(".docx"):
        raise ValidationAppError("Only Word (.docx) files are accepted for a document template.")

    storage_key, original_filename, size_bytes = save_upload(file, STORAGE_SUBDIRECTORY)

    template = DocumentTemplate(
        document_type=document_type,
        storage_key=storage_key,
        original_filename=original_filename,
        file_size_bytes=size_bytes,
        uploaded_by=actor_id,
        # The first template uploaded for a type becomes its default
        # automatically -- otherwise "Download Document" would 404 with
        # no default configured until an admin remembers to set one.
        is_default=get_default(db, document_type) is None,
    )
    db.add(template)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, f"{document_type} template uploaded", actor_id, new_value=original_filename
    )
    db.commit()
    db.refresh(template)
    return template


def set_default(db: Session, template_id: int, actor_id: int) -> DocumentTemplate:
    template = get_template(db, template_id)
    if template.is_default:
        return template
    db.query(DocumentTemplate).filter(
        DocumentTemplate.document_type == template.document_type,
        DocumentTemplate.is_default.is_(True),
    ).update({"is_default": False})
    template.is_default = True
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, f"{template.document_type} default template changed", actor_id,
        new_value=template.original_filename,
    )
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: int, actor_id: int) -> None:
    template = get_template(db, template_id)
    if template.is_default:
        raise ValidationAppError(
            "This is the default template for its document type. Set another template as default first."
        )
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, f"{template.document_type} template deleted", actor_id,
        previous_value=template.original_filename,
    )
    template.deleted_at = datetime.now(timezone.utc)
    db.commit()


def _render_docx(storage_key: str, context: dict) -> bytes:
    path = resolve_path(storage_key)
    try:
        doc = DocxTemplate(str(path))
        doc.render(context)
    except Exception as exc:
        raise ValidationAppError(
            f"The uploaded template couldn't be merged -- check its placeholder syntax. ({exc})"
        ) from exc
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def render_quotation_document(db: Session, quotation: Quotation) -> tuple[bytes, str]:
    from app.services import quotation_service

    template = get_default(db, "Quotation")
    if template is None:
        raise ValidationAppError(
            "No default Quotation template is configured. Upload one in Administration > Documents."
        )

    project = db.query(Project).filter(Project.id == quotation.project_id).first()
    client = (
        db.query(Client).filter(Client.id == project.client_id).first()
        if project is not None
        else None
    )
    line_items = quotation_service.get_line_items(db, quotation.id)
    subtotal = sum((Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) for i in line_items), Decimal("0"))

    context = {
        "quotation_no": quotation.quotation_no,
        "revision": quotation.revision,
        "issue_date": quotation.issue_date.strftime("%d %B %Y"),
        "validity": quotation.validity.strftime("%d %B %Y"),
        "status": quotation.status,
        "currency": quotation.currency,
        "prepared_by": _user_name(db, quotation.prepared_by),
        "client_name": client.company_name if client else "",
        "project_name": project.project_name if project else "",
        "project_no": project.project_no if project else "",
        "line_items": [
            {
                "description": item.description,
                "quantity": f"{float(item.quantity):g}",
                "unit_price": f"{float(item.unit_price):.2f}",
                "amount": f"{float(item.quantity) * float(item.unit_price):.2f}",
            }
            for item in line_items
        ],
        "subtotal": f"{subtotal:.2f}",
        "discount_amount": f"{float(quotation.discount_amount):.2f}",
        "amount": f"{float(quotation.amount):.2f}",
        "notes": _plain_text(quotation.notes),
        "terms_and_conditions": [_plain_text(term) for term in quotation.terms_and_conditions],
    }
    filename = f"{quotation.quotation_no}.docx"
    return _render_docx(template.storage_key, context), filename


def render_contract_document(db: Session, contract: Contract) -> tuple[bytes, str]:
    from app.services import contract_service

    template = get_default(db, "Contract")
    if template is None:
        raise ValidationAppError(
            "No default Contract template is configured. Upload one in Administration > Documents."
        )

    project = db.query(Project).filter(Project.id == contract.project_id).first()
    client = (
        db.query(Client).filter(Client.id == project.client_id).first()
        if project is not None
        else None
    )
    clauses = contract_service.get_clauses(db, contract.id)

    context = {
        "contract_no": contract.contract_no,
        "revision": contract.revision,
        "currency": contract.currency,
        "contract_value": f"{float(contract.contract_value):.2f}",
        "issue_date": contract.issue_date.strftime("%d %B %Y"),
        "signed_date": contract.signed_date.strftime("%d %B %Y") if contract.signed_date else "",
        "expiry_date": contract.expiry_date.strftime("%d %B %Y"),
        "status": contract.status,
        "prepared_by": _user_name(db, contract.prepared_by),
        "client_representative": contract.client_representative,
        "client_name": client.company_name if client else "",
        "project_name": project.project_name if project else "",
        "project_no": project.project_no if project else "",
        "scope_summary": _plain_text(contract.scope_summary),
        "clauses": [{"title": c.title, "content": _plain_text(c.content)} for c in clauses],
    }
    filename = f"{contract.contract_no}.docx"
    return _render_docx(template.storage_key, context), filename
