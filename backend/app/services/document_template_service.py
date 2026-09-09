"""Admin-uploaded .docx templates for Quotation/Contract/Payment Plan
documents.

An Administrator uploads a .docx per (document_type, language) --
Quotation, Contract, or Payment Plan (migration 0085), English or
Arabic -- under Administration > Documents and marks one as the default
for that pair (migration 0064: each document_type carries two defaults
side by side, not one shared one). When a project's Quotation/Contract/
Payment Plan tab asks for the actual document, the requested language's
default template's placeholders ({{ field }}, and {%tr for ... %} row
loops inside a table -- both standard docxtpl/Jinja2 syntax) are merged
with that record's live data via render_quotation_document/
render_contract_document/render_payment_plan_document below, and the
merged .docx is the download.

render_quotation_pdf/render_contract_pdf/render_payment_plan_pdf below
convert that same merged .docx to PDF (via _docx_to_pdf) so "Print" and
"Email" can use the identical, admin-configured template instead of the
separate hardcoded on-screen preview (QuotationPreview.vue/
ContractPreview.vue) those actions used to print. _docx_to_pdf reads the
template's own `language`
to decide text direction/font rather than always assuming Arabic --
previously every rendered PDF was forced right-to-left with an Arabic
font even when the uploaded template (and its content) was plain
English.
"""

import base64
import copy
import html
import io
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docxtpl import DocxTemplate, InlineImage
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.file_storage import resolve_path, save_upload
from app.core.number_to_words import amount_to_words
from app.models.client import Client
from app.models.contract import Contract
from app.models.document_template import DOCUMENT_TEMPLATE_LANGUAGES, DOCUMENT_TEMPLATE_TYPES, DocumentTemplate
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.user import User
from app.services import audit_service, company_service
from app.services.pdf_render import FONT_PATH

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


def _check_language(language: str) -> None:
    if language not in DOCUMENT_TEMPLATE_LANGUAGES:
        raise ValidationAppError(f"language must be one of {DOCUMENT_TEMPLATE_LANGUAGES}")


def list_templates(db: Session, document_type: str | None = None, language: str | None = None) -> list[DocumentTemplate]:
    query = db.query(DocumentTemplate).filter(DocumentTemplate.deleted_at.is_(None))
    if document_type is not None:
        _check_document_type(document_type)
        query = query.filter(DocumentTemplate.document_type == document_type)
    if language is not None:
        _check_language(language)
        query = query.filter(DocumentTemplate.language == language)
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


def get_default(db: Session, document_type: str, language: str) -> DocumentTemplate | None:
    _check_document_type(document_type)
    _check_language(language)
    return (
        db.query(DocumentTemplate)
        .filter(
            DocumentTemplate.document_type == document_type,
            DocumentTemplate.language == language,
            DocumentTemplate.is_default.is_(True),
            DocumentTemplate.deleted_at.is_(None),
        )
        .first()
    )


def upload_template(db: Session, document_type: str, language: str, file, actor_id: int) -> DocumentTemplate:
    _check_document_type(document_type)
    _check_language(language)
    if not (file.filename or "").lower().endswith(".docx"):
        raise ValidationAppError("Only Word (.docx) files are accepted for a document template.")

    storage_key, original_filename, size_bytes = save_upload(file, STORAGE_SUBDIRECTORY)

    # Every upload becomes this (type, language) pair's active default
    # immediately -- not just the first one. Leaving a re-upload inactive
    # until someone remembered a separate "Set Default" click was a real
    # trap: every generated document silently kept using whatever old
    # template was still flagged default, with no indication anything
    # was wrong, until an admin happened to notice. "Set Default" (see
    # set_default below) still exists for deliberately reverting to an
    # older upload later.
    db.query(DocumentTemplate).filter(
        DocumentTemplate.document_type == document_type,
        DocumentTemplate.language == language,
        DocumentTemplate.is_default.is_(True),
    ).update({"is_default": False})

    template = DocumentTemplate(
        document_type=document_type,
        language=language,
        storage_key=storage_key,
        original_filename=original_filename,
        file_size_bytes=size_bytes,
        uploaded_by=actor_id,
        is_default=True,
    )
    db.add(template)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, f"{document_type} ({language}) template uploaded", actor_id,
        new_value=original_filename,
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
        DocumentTemplate.language == template.language,
        DocumentTemplate.is_default.is_(True),
    ).update({"is_default": False})
    template.is_default = True
    audit_service.log_event(
        db, ENTITY_TYPE, template.id, f"{template.document_type} ({template.language}) default template changed",
        actor_id, new_value=template.original_filename,
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


def _get_company_logo_path(db: Session) -> Path | None:
    """The company-wide logo (Administration > Company), if one has been
    uploaded -- see company_service.upload_logo. Shared by every
    template/document_type/language rather than uploaded per-template:
    there is exactly one letterhead logo, and any template's {{ logo }}
    merge field (see MERGE_FIELD_CATALOG below) refers to this same
    file."""
    settings = company_service.get_settings(db)
    if not settings.logo_storage_key:
        return None
    return resolve_path(settings.logo_storage_key)


def _render_docx(storage_key: str, context: dict, logo_path: Path | None) -> bytes:
    path = resolve_path(storage_key)
    try:
        doc = DocxTemplate(str(path))
        # {{ logo }} uses the exact same {{ field }} syntax as every text
        # field in MERGE_FIELD_CATALOG -- docxtpl draws an actual image at
        # that spot because the context value is an InlineImage instance,
        # not because the placeholder is written any differently. Empty
        # string (not omitted) when there's no logo yet, so a template
        # that already has {{ logo }} placed renders cleanly rather than
        # failing on an undefined Jinja variable.
        context = {**context, "logo": InlineImage(doc, str(logo_path), width=Mm(35)) if logo_path else ""}
        doc.render(context)
    except Exception as exc:
        raise ValidationAppError(
            f"The uploaded template couldn't be merged -- check its placeholder syntax. ({exc})"
        ) from exc
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# (direction, text-align, primary font stack) per template language --
# NotoNaskhArabic is always loaded and always in the stack (as a fallback
# for English, primary for Arabic) so embedded Arabic text (a client's
# Arabic name, say) never renders as tofu boxes regardless of which one
# the template's own static text is written in.
_PDF_STYLE_BY_LANGUAGE = {
    "Arabic": ("rtl", "right", "'NotoNaskhArabic', sans-serif"),
    "English": ("ltr", "left", "'Helvetica Neue', Arial, 'NotoNaskhArabic', sans-serif"),
}

_ALIGN_CSS = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
}


def _run_image_html(run) -> str | None:
    """A run's <w:drawing> as a base64-embedded <img>, sized from the
    drawing's own EMU extent (1 EMU = 1/914400in -> px at 96dpi is
    EMU/9525) -- covers both an inline picture and a floating/anchored
    one (e.g. a letterhead logo positioned beside the title text) the
    same way, since docx stores the extent identically either way.
    Returns None for a run with no drawing, or one whose image part
    can't be resolved (never expected in practice, but a merge field's
    run should never hard-fail a whole document over one bad image)."""
    drawing = run._r.find(qn("w:drawing"))
    if drawing is None:
        return None
    blip = drawing.find(f".//{qn('a:blip')}")
    if blip is None:
        return None
    r_id = blip.get(qn("r:embed"))
    if not r_id:
        return None
    try:
        part = run.part.related_parts[r_id]
    except KeyError:
        return None
    style = ""
    extent = drawing.find(f".//{qn('wp:extent')}")
    if extent is not None and extent.get("cx"):
        width_px = int(extent.get("cx")) / 9525
        style = f' style="width:{width_px:.1f}px;max-width:100%;"'
    encoded = base64.b64encode(part.blob).decode("ascii")
    return f'<img src="data:{part.content_type};base64,{encoded}"{style}>'


def _run_html(run) -> str:
    """One run's exact character formatting (bold/italic/underline,
    explicit font color, explicit font size) as an inline-styled
    <span>, or its image if it carries one instead of text -- the
    template's own direct formatting on a merge field's run (see
    MERGE_FIELD_CATALOG/apply_mapping: mapping a field preserves the
    run it replaces text in) survives into the PDF this way, not just
    into the .docx download."""
    image_html = _run_image_html(run)
    if image_html is not None:
        return image_html
    text = html.escape(run.text or "")
    if not text:
        return ""
    text = text.replace("\n", "<br>").replace("\t", "&emsp;")
    styles: list[str] = []
    if run.font.bold:
        styles.append("font-weight:bold")
    if run.font.italic:
        styles.append("font-style:italic")
    if run.font.underline:
        styles.append("text-decoration:underline")
    try:
        color = run.font.color.rgb if run.font.color is not None else None
    except AttributeError:
        color = None
    if color:
        styles.append(f"color:#{color}")
    if run.font.size:
        styles.append(f"font-size:{run.font.size.pt:g}pt")
    return f'<span style="{";".join(styles)}">{text}</span>' if styles else text


def _has_num_pr(pPr) -> bool:
    return pPr is not None and pPr.find(qn("w:numPr")) is not None


def _is_list_paragraph(paragraph: Paragraph) -> bool:
    """Whether this paragraph uses Word's own numbered/bulleted-list
    formatting -- common for a template's Terms & Conditions/Clauses
    (see MERGE_FIELD_CATALOG's repeating_list fields: each loop
    iteration is one paragraph, and an admin authoring those as a real
    Word list, not manually typed dashes, is the expected case). Not
    tied to which numbering definition/level it uses -- a single
    bullet-point treatment for any list paragraph is a reasonable
    approximation short of reading numbering.xml's actual list styles.

    <w:numPr> can live directly on the paragraph, but for a paragraph
    using a named list style (e.g. Word's own "List Bullet", what
    add_paragraph(style=...) produces, and the common case for a
    template authored by clicking Word's bullet-list toolbar button)
    it instead lives on that style's own <w:pPr> in styles.xml, not on
    the paragraph itself -- checked here too, one level, not walking a
    w:basedOn chain further up."""
    if _has_num_pr(paragraph._p.find(qn("w:pPr"))):
        return True
    style = paragraph.style
    return style is not None and _has_num_pr(style.element.find(qn("w:pPr")))


def _paragraph_html(paragraph: Paragraph) -> str:
    runs_html = "".join(_run_html(run) for run in paragraph.runs)
    align = _ALIGN_CSS.get(paragraph.alignment)
    styles = [f"text-align:{align}"] if align else []
    prefix = ""
    if _is_list_paragraph(paragraph):
        styles.append("margin-inline-start:1.5em")
        prefix = "&bull;&nbsp;"
    style = f' style="{";".join(styles)};"' if styles else ""
    return f"<p{style}>{prefix}{runs_html}</p>"


def _cell_style(cell: _Cell) -> str:
    """A table cell's own background shading (<w:shd>), the one piece
    of direct table formatting distinctive enough to matter visually
    (e.g. a dark header row with white text) -- borders stay the flat
    `td, th` rule below rather than reading each cell's own border
    spec, a reasonable approximation for the plain grid lines almost
    every uploaded template's tables actually use."""
    tc_pr = cell._tc.find(qn("w:tcPr"))
    shading = tc_pr.find(qn("w:shd")) if tc_pr is not None else None
    fill = shading.get(qn("w:fill")) if shading is not None else None
    if fill and fill.upper() != "AUTO":
        return f' style="background-color:#{fill};"'
    return ""


def _table_html(table: Table) -> str:
    rows_html = []
    for row in table.rows:
        cells_html = [
            f"<td{_cell_style(cell)}>{''.join(_paragraph_html(p) for p in cell.paragraphs)}</td>"
            for cell in row.cells
        ]
        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")
    return f"<table>{''.join(rows_html)}</table>"


def _docx_to_html(document) -> str:
    """The merged document's body, rendered directly from its own
    python-docx object tree (paragraphs/runs/tables, walked the same
    "one block at a time, in document order" way as _body_blocks
    below, reused here) rather than through a generic docx->HTML
    converter -- see _docx_to_pdf's docstring for why."""
    parts = []
    for _, kind, wrapper in _body_blocks(document):
        parts.append(_paragraph_html(wrapper) if kind == "paragraph" else _table_html(wrapper))
    return "".join(parts)


def _docx_to_pdf(docx_bytes: bytes, language: str) -> bytes:
    """Converts a merged .docx to a real, selectable-text PDF for
    Print/Email, reusing the exact stack pdf_render.py already relies on
    for Government Forms (WeasyPrint + the bundled Noto Naskh Arabic
    font) rather than adding a new system dependency. _docx_to_html
    above renders the document's own paragraphs/runs/tables straight
    from python-docx -- the same library already used elsewhere in this
    file for the field-mapping tool -- into HTML that keeps each run's
    own bold/italic/underline/color/size and each table cell's own
    background shading, plus every embedded image (inline or
    floating/anchored, e.g. a letterhead logo), not just the paragraph/
    table structure a generic docx->HTML library would keep. A
    LibreOffice-headless docx->PDF conversion was tried before this and
    does not run reliably in this app's container, so this stays a
    pure-Python round-trip through WeasyPrint rather than shelling out
    to it.

    Direction/alignment/font follow the template's own declared
    `language` (DocumentTemplate.language) rather than always assuming
    Arabic -- previously this forced right-to-left with an Arabic font
    on every document, English ones included."""
    direction, text_align, font_stack = _PDF_STYLE_BY_LANGUAGE[language]
    html_lang = "ar" if language == "Arabic" else "en"
    document = Document(io.BytesIO(docx_bytes))
    body_html = _docx_to_html(document)
    html_doc = f"""<!DOCTYPE html>
<html dir="{direction}" lang="{html_lang}">
<head>
<meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'NotoNaskhArabic';
    src: url('file://{FONT_PATH}');
  }}
  @page {{ size: A4; margin: 2.5cm 2cm; }}
  body {{
    font-family: {font_stack};
    direction: {direction};
    text-align: {text_align};
    font-size: 12pt;
    line-height: 1.8;
    color: #1a1a2e;
  }}
  table {{ width: 100%; border-collapse: collapse; margin: 0 0 1em; }}
  td, th {{ border: 1px solid #999; padding: 0.4em 0.6em; }}
  p {{ margin: 0 0 0.8em; }}
  img {{ display: block; }}
</style>
</head>
<body>{body_html}</body>
</html>"""
    return HTML(string=html_doc).write_pdf()


def _resolve_language(db: Session, language: str | None) -> str:
    """Falls back to CompanySettings.default_language when the caller
    (an API endpoint that lets staff pick, or one that doesn't expose the
    choice at all) doesn't specify one -- same "explicit choice wins,
    company-wide setting otherwise" pattern already established for
    quotation/contract currency defaults."""
    if language is not None:
        _check_language(language)
        return language
    return company_service.get_settings(db).default_language


def render_quotation_document(db: Session, quotation: Quotation, language: str | None = None) -> tuple[bytes, str]:
    from app.services import quotation_service

    language = _resolve_language(db, language)
    template = get_default(db, "Quotation", language)
    if template is None:
        raise ValidationAppError(
            f"No default {language} Quotation template is configured. Upload one in Administration > Documents."
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
        "project_address": (project.site_address or "") if project else "",
        "amount_in_words": amount_to_words(Decimal(str(quotation.amount)), quotation.currency),
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
        "scope_phases": [_plain_text(phase) for phase in quotation.scope_phases],
        "payment_terms": [_plain_text(term) for term in quotation.payment_terms],
    }
    filename = f"{quotation.quotation_no}.docx"
    return _render_docx(template.storage_key, context, _get_company_logo_path(db)), filename


def render_quotation_pdf(db: Session, quotation: Quotation, language: str | None = None) -> tuple[bytes, str]:
    """Same merged document as render_quotation_document, converted to
    PDF -- what Print and Email actually use, so both show the admin's
    real uploaded template rather than a separate hardcoded preview."""
    language = _resolve_language(db, language)
    content, filename = render_quotation_document(db, quotation, language)
    return _docx_to_pdf(content, language), filename.removesuffix(".docx") + ".pdf"


def render_contract_document(db: Session, contract: Contract, language: str | None = None) -> tuple[bytes, str]:
    from app.services import contract_service

    language = _resolve_language(db, language)
    template = get_default(db, "Contract", language)
    if template is None:
        raise ValidationAppError(
            f"No default {language} Contract template is configured. Upload one in Administration > Documents."
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
        "project_address": (project.site_address or "") if project else "",
        "amount_in_words": amount_to_words(Decimal(str(contract.contract_value)), contract.currency),
        "scope_summary": _plain_text(contract.scope_summary),
        "clauses": [{"title": c.title, "content": _plain_text(c.content)} for c in clauses],
    }
    filename = f"{contract.contract_no}.docx"
    return _render_docx(template.storage_key, context, _get_company_logo_path(db)), filename


def render_contract_pdf(db: Session, contract: Contract, language: str | None = None) -> tuple[bytes, str]:
    """PDF counterpart of render_contract_document -- see
    render_quotation_pdf's docstring."""
    language = _resolve_language(db, language)
    content, filename = render_contract_document(db, contract, language)
    return _docx_to_pdf(content, language), filename.removesuffix(".docx") + ".pdf"


def render_payment_plan_document(db: Session, project: Project, language: str | None = None) -> tuple[bytes, str]:
    """Unlike Quotation/Contract, a project's payment plan isn't one
    record -- it's up to two FinancialAgreements (one per billing
    stream, see AGREEMENT_STREAMS), each with its own obligations
    schedule. This merges whichever streams the project actually has an
    agreement for into a single document: one summary row per stream in
    `streams`, and every obligation across all of them (tagged with its
    stream) in one flat `schedule` table -- a stream with no agreement
    yet is simply absent from both, rather than rendered empty."""
    from app.models.payment import AGREEMENT_STREAMS
    from app.services import payment_service

    language = _resolve_language(db, language)
    template = get_default(db, "Payment Plan", language)
    if template is None:
        raise ValidationAppError(
            f"No default {language} Payment Plan template is configured. Upload one in Administration > Documents."
        )

    client = db.query(Client).filter(Client.id == project.client_id).first()

    streams: list[dict] = []
    schedule: list[dict] = []
    for stream in AGREEMENT_STREAMS:
        agreement = payment_service.get_agreement_by_project(db, project.project_no, stream)
        if agreement is None:
            continue
        streams.append({
            "stream": stream,
            "status": agreement.status,
            "amount": f"{float(agreement.contract_amount):.2f}",
            "currency": agreement.currency,
            "payment_mode": agreement.payment_mode,
            "agreement_date": agreement.agreement_date.strftime("%d %B %Y"),
            "start_date": agreement.contract_start_date.strftime("%d %B %Y"),
        })
        for obligation in payment_service.get_obligations(db, agreement.id):
            schedule.append({
                "stream": stream,
                "sequence_number": str(obligation.sequence_number),
                "description": obligation.description,
                "amount_due": f"{float(obligation.amount_due):.2f}",
                "currency": agreement.currency,
                "due_date": obligation.due_date.strftime("%d %B %Y"),
            })

    context = {
        "project_name": project.project_name,
        "project_no": project.project_no,
        "project_address": project.site_address or "",
        "client_name": client.company_name if client else "",
        "issue_date": datetime.now(timezone.utc).strftime("%d %B %Y"),
        "streams": streams,
        "schedule": schedule,
    }
    filename = f"{project.project_no}-Payment-Plan.docx"
    return _render_docx(template.storage_key, context, _get_company_logo_path(db)), filename


def render_payment_plan_pdf(db: Session, project: Project, language: str | None = None) -> tuple[bytes, str]:
    """PDF counterpart of render_payment_plan_document -- see
    render_quotation_pdf's docstring."""
    language = _resolve_language(db, language)
    content, filename = render_payment_plan_document(db, project, language)
    return _docx_to_pdf(content, language), filename.removesuffix(".docx") + ".pdf"


# --- Visual field mapping -- lets an admin click a spot in an uploaded
# template and place a merge field there instead of hand-typing {{ field
# }}/{%tr %} syntax into Word. The catalog below is the single source of
# truth for what a template can reference; it must stay in lockstep with
# the context dicts render_quotation_document/render_contract_document
# actually build above, since _sample_context's save-time validation
# render is only as meaningful as that agreement.
MERGE_FIELD_CATALOG: dict[str, list[dict]] = {
    "Quotation": [
        # Same {{ field }} syntax as every other text field -- see
        # _render_docx: docxtpl draws an actual image here because the
        # context value is an InlineImage, not because this placeholder
        # is written any differently. Renders as nothing if no company
        # logo has been uploaded yet (Administration > Company).
        {"key": "logo", "label": "Company Logo", "kind": "text"},
        {"key": "quotation_no", "label": "Quotation No.", "kind": "text"},
        {"key": "revision", "label": "Revision", "kind": "text"},
        {"key": "issue_date", "label": "Issue Date", "kind": "text"},
        {"key": "validity", "label": "Valid Until", "kind": "text"},
        {"key": "status", "label": "Status", "kind": "text"},
        {"key": "currency", "label": "Currency", "kind": "text"},
        {"key": "prepared_by", "label": "Prepared By", "kind": "text"},
        {"key": "client_name", "label": "Client Name", "kind": "text"},
        {"key": "project_name", "label": "Project Name", "kind": "text"},
        {"key": "project_no", "label": "Project No.", "kind": "text"},
        {"key": "project_address", "label": "Project/Site Address", "kind": "text"},
        {"key": "subtotal", "label": "Subtotal", "kind": "text"},
        {"key": "discount_amount", "label": "Discount Amount", "kind": "text"},
        {"key": "amount", "label": "Total Amount", "kind": "text"},
        {"key": "amount_in_words", "label": "Total Amount (in Words)", "kind": "text"},
        {"key": "notes", "label": "Notes", "kind": "text"},
        {
            "key": "line_items",
            "label": "Line Items",
            "kind": "repeating_table",
            "loopVar": "item",
            "columns": [
                {"key": "description", "label": "Description"},
                {"key": "quantity", "label": "Quantity"},
                {"key": "unit_price", "label": "Unit Price"},
                {"key": "amount", "label": "Amount"},
            ],
        },
        {"key": "terms_and_conditions", "label": "Terms & Conditions", "kind": "repeating_list", "loopVar": "term"},
        {"key": "scope_phases", "label": "Scope Phases", "kind": "repeating_list", "loopVar": "phase"},
        {"key": "payment_terms", "label": "Payment Terms", "kind": "repeating_list", "loopVar": "term"},
    ],
    "Contract": [
        {"key": "logo", "label": "Company Logo", "kind": "text"},
        {"key": "contract_no", "label": "Contract No.", "kind": "text"},
        {"key": "revision", "label": "Revision", "kind": "text"},
        {"key": "currency", "label": "Currency", "kind": "text"},
        {"key": "contract_value", "label": "Contract Value", "kind": "text"},
        {"key": "issue_date", "label": "Issue Date", "kind": "text"},
        {"key": "signed_date", "label": "Signed Date", "kind": "text"},
        {"key": "expiry_date", "label": "Expiry Date", "kind": "text"},
        {"key": "status", "label": "Status", "kind": "text"},
        {"key": "prepared_by", "label": "Prepared By", "kind": "text"},
        {"key": "client_representative", "label": "Client Representative", "kind": "text"},
        {"key": "client_name", "label": "Client Name", "kind": "text"},
        {"key": "project_name", "label": "Project Name", "kind": "text"},
        {"key": "project_no", "label": "Project No.", "kind": "text"},
        {"key": "project_address", "label": "Project/Site Address", "kind": "text"},
        {"key": "amount_in_words", "label": "Contract Value (in Words)", "kind": "text"},
        {"key": "scope_summary", "label": "Scope Summary", "kind": "text"},
        {
            "key": "clauses",
            "label": "Clauses",
            "kind": "repeating_table",
            "loopVar": "clause",
            "columns": [
                {"key": "title", "label": "Title"},
                {"key": "content", "label": "Content"},
            ],
        },
    ],
    "Payment Plan": [
        {"key": "logo", "label": "Company Logo", "kind": "text"},
        {"key": "project_name", "label": "Project Name", "kind": "text"},
        {"key": "project_no", "label": "Project No.", "kind": "text"},
        {"key": "project_address", "label": "Project/Site Address", "kind": "text"},
        {"key": "client_name", "label": "Client Name", "kind": "text"},
        {"key": "issue_date", "label": "Issue Date", "kind": "text"},
        {
            "key": "streams",
            "label": "Plan Summary (one row per billing stream)",
            "kind": "repeating_table",
            "loopVar": "plan",
            "columns": [
                {"key": "stream", "label": "Stream"},
                {"key": "status", "label": "Status"},
                {"key": "amount", "label": "Total Amount"},
                {"key": "currency", "label": "Currency"},
                {"key": "payment_mode", "label": "Payment Mode"},
                {"key": "agreement_date", "label": "Agreement Date"},
                {"key": "start_date", "label": "Start Date"},
            ],
        },
        {
            "key": "schedule",
            "label": "Payment Schedule (every installment, all streams)",
            "kind": "repeating_table",
            "loopVar": "row",
            "columns": [
                {"key": "stream", "label": "Stream"},
                {"key": "sequence_number", "label": "No."},
                {"key": "description", "label": "Installment"},
                {"key": "amount_due", "label": "Amount"},
                {"key": "currency", "label": "Currency"},
                {"key": "due_date", "label": "Due Date"},
            ],
        },
    ],
}

_FIELD_BY_KEY: dict[str, dict[str, dict]] = {
    doc_type: {field["key"]: field for field in fields} for doc_type, fields in MERGE_FIELD_CATALOG.items()
}


def get_merge_fields(document_type: str) -> list[dict]:
    _check_document_type(document_type)
    return MERGE_FIELD_CATALOG[document_type]


_MERGE_TOKEN_RE = re.compile(r"\{\{\s*[A-Za-z_][\w.]*\s*\}\}")


def _split_merge_tokens(text: str) -> list[tuple[str, bool]]:
    """Splits `text` into (segment, is_token) pieces at every `{{
    field }}` / `{{ item.column }}` merge-field token -- used by
    _set_paragraph_text so each token can be written into its own run,
    separate from the template's static wording around it. Doesn't
    touch `{%p ... %}`/`{%tr ... %}` repeating-block markers (a
    different syntax, and those live in their own throwaway
    paragraphs/rows -- see _marker_paragraph_element/_clone_marker_row
    -- never inside a mapped block's own text). Empty input, or text
    with no tokens at all, still yields exactly one segment so the
    common case (no fields, or a token-free static line) round-trips
    to a single plain run, same as before this existed."""
    segments: list[tuple[str, bool]] = []
    pos = 0
    for match in _MERGE_TOKEN_RE.finditer(text):
        if match.start() > pos:
            segments.append((text[pos : match.start()], False))
        segments.append((match.group(0), True))
        pos = match.end()
    if pos < len(text) or not segments:
        segments.append((text[pos:], False))
    return segments


def _set_paragraph_text(paragraph: Paragraph, text: str) -> None:
    """Rewrites a paragraph's *text* runs to hold `text`, preserving
    the first existing text run's character formatting (bold, font,
    etc.) as a base for every new run. A deliberate simplification --
    a paragraph that mixed multiple run styles mid-sentence collapses
    to one base style -- far more robust than trying to splice text in
    while preserving every original run boundary, and irrelevant for
    the short, mostly-plain lines a merge field actually lives in.

    Every `{{ field }}` merge-field token in `text` (see
    _split_merge_tokens) gets its own run, on top of that base style
    plus bold -- so once a real document is rendered from this saved
    template, the *entered* value stands out from the template's own
    static wording without the admin ever hand-formatting anything.
    docxtpl's plain-text substitution only replaces a run's text, not
    its formatting, so the token's run staying bold is what makes the
    merged value come out bold; the static wording around it, in its
    own separate run, is untouched. (RichText -- inline bold
    formatting passed in the merge *data* itself rather than baked
    into the saved template -- was tried and rejected: it works by
    splicing raw XML into a run's text mid-render, which only produces
    valid OOXML when that run holds nothing but the token, and every
    run this service writes always holds a full mapped paragraph's
    text, tokens and static wording together, so it corrupted the
    document as soon as a token shared a paragraph with any other
    text.)

    Any run containing a <w:drawing> or legacy VML <w:pict> (an image
    -- e.g. a company logo sharing this paragraph with the
    company-name text next to it, a common letterhead layout) is left
    untouched rather than swept up with the text runs: a real uploaded
    template's own embedded picture has to survive an admin mapping
    this paragraph to a field just as reliably as it survives the
    actual docxtpl merge later (see _render_docx's own comment --
    docxtpl itself never touches non-Jinja content, so this is the one
    place in the mapping tool that used to be able to destroy it)."""
    runs = list(paragraph.runs)
    text_runs = [run for run in runs if run._r.find(qn("w:drawing")) is None and run._r.find(qn("w:pict")) is None]
    had_drawing = len(text_runs) != len(runs)

    preserved_rpr = None
    if text_runs:
        existing_rpr = text_runs[0]._r.find(qn("w:rPr"))
        if existing_rpr is not None:
            preserved_rpr = copy.deepcopy(existing_rpr)
    for run in text_runs:
        run._r.getparent().remove(run._r)

    if not text and had_drawing:
        # Nothing to write and the paragraph still holds its image --
        # don't add a stray empty run on top of it.
        return

    for segment, is_token in _split_merge_tokens(text):
        new_run = OxmlElement("w:r")
        run_rpr = copy.deepcopy(preserved_rpr) if preserved_rpr is not None else None
        if is_token:
            if run_rpr is None:
                run_rpr = OxmlElement("w:rPr")
            if run_rpr.find(qn("w:b")) is None:
                run_rpr.append(OxmlElement("w:b"))
        if run_rpr is not None:
            new_run.append(run_rpr)
        new_text_el = OxmlElement("w:t")
        new_text_el.set(qn("xml:space"), "preserve")
        new_text_el.text = segment
        new_run.append(new_text_el)
        paragraph._p.append(new_run)


def _marker_paragraph_element(tag_text: str):
    """A bare, unstyled paragraph holding one docxtpl {%p %}/{%tr %} tag
    -- used as a disposable before/after marker, never seen by anyone:
    docxtpl's preprocessing deletes the entire <w:p>/<w:tr> a tag like
    this is found in and replaces it with just the bare Jinja tag (see
    the module-level docxtpl docs), so this element's own formatting
    never survives to be seen."""
    p = OxmlElement("w:p")
    run = OxmlElement("w:r")
    text_el = OxmlElement("w:t")
    text_el.set(qn("xml:space"), "preserve")
    text_el.text = tag_text
    run.append(text_el)
    p.append(run)
    return p


def _clone_marker_row(row, marker_text: str):
    """A row-shaped clone of `row` (same cell count/widths/borders) with
    every cell's text cleared and one docxtpl {%tr %} marker tag written
    into its first cell. Needs a whole extra row rather than just text
    inside the marked row itself: docxtpl deletes the ENTIRE <w:tr> a
    {%tr %} tag is found in, replacing it with the bare Jinja tag -- the
    marked row itself is left as an ordinary row and is what actually
    repeats, so the for/endfor tags need their own throwaway rows
    immediately before/after it, not to live inside it."""
    cloned_element = copy.deepcopy(row._tr)
    cloned_row = type(row)(cloned_element, row._parent)
    for cell in cloned_row.cells:
        for paragraph in cell.paragraphs:
            _set_paragraph_text(paragraph, "")
    if cloned_row.cells and cloned_row.cells[0].paragraphs:
        _set_paragraph_text(cloned_row.cells[0].paragraphs[0], marker_text)
    return cloned_element


def _body_blocks(document) -> list[tuple[int, str, object]]:
    """(blockIndex, kind, wrapper) for every top-level paragraph/table in
    the document body, in document order -- extract_layout and
    apply_mapping both walk this exact same way, so a blockIndex always
    means the same block between the two calls (nothing changes the
    docx's own body structure in between; only text within existing
    blocks/cells does)."""
    blocks: list[tuple[int, str, object]] = []
    index = 0
    for child in document.element.body:
        if child.tag == qn("w:p"):
            blocks.append((index, "paragraph", Paragraph(child, document)))
            index += 1
        elif child.tag == qn("w:tbl"):
            blocks.append((index, "table", Table(child, document)))
            index += 1
    return blocks


def extract_layout(storage_key: str) -> dict:
    """The uploaded template's paragraphs/tables, in document order, as
    plain editable text -- what the admin's field-mapping screen shows
    and edits. Only a table cell's first paragraph is exposed (a cell
    with more than one paragraph is the rare case, and editing just the
    first is a reasonable simplification for a merge-field target)."""
    document = Document(str(resolve_path(storage_key)))
    blocks: list[dict] = []
    for block_index, kind, wrapper in _body_blocks(document):
        if kind == "paragraph":
            blocks.append({"kind": "paragraph", "blockIndex": block_index, "text": wrapper.text, "repeatingField": None})
        else:
            rows = []
            for row_index, row in enumerate(wrapper.rows):
                cells = [
                    {"cellIndex": cell_index, "text": cell.paragraphs[0].text if cell.paragraphs else ""}
                    for cell_index, cell in enumerate(row.cells)
                ]
                rows.append({"rowIndex": row_index, "cells": cells, "repeatingField": None})
            blocks.append({"kind": "table", "blockIndex": block_index, "rows": rows})
    return {"blocks": blocks}


def apply_mapping(storage_key: str, document_type: str, blocks: list[dict]) -> bytes:
    """Writes the admin's edited text back into the template (one plain
    run per paragraph/cell -- see _set_paragraph_text), then, for at
    most one paragraph and one table row across the whole document,
    wraps it in docxtpl's repeating-block marker tags if it was flagged
    `repeatingField` -- see _clone_marker_row/_marker_paragraph_element
    for why that needs extra rows/paragraphs rather than editing in
    place. A second block flagged for the same or another repeating
    field is simply ignored (last one processed in document order wins
    for a given kind) rather than erroring -- the frontend's palette
    only ever lets one location hold a given repeating field at a time,
    so this only matters for a payload assembled by hand."""
    _check_document_type(document_type)
    document = Document(str(resolve_path(storage_key)))
    by_index = {index: (kind, wrapper) for index, kind, wrapper in _body_blocks(document)}

    repeating_paragraph: Paragraph | None = None
    repeating_paragraph_field: dict | None = None
    repeating_row = None
    repeating_row_field: dict | None = None

    for block in blocks:
        located = by_index.get(block.get("blockIndex"))
        if located is None:
            continue
        kind, wrapper = located
        if kind != block.get("kind"):
            continue

        if kind == "paragraph":
            _set_paragraph_text(wrapper, block.get("text") or "")
            field_key = block.get("repeatingField")
            if field_key and field_key in _FIELD_BY_KEY[document_type]:
                repeating_paragraph = wrapper
                repeating_paragraph_field = _FIELD_BY_KEY[document_type][field_key]
        else:
            for row_payload in block.get("rows") or []:
                row_index = row_payload.get("rowIndex")
                if row_index is None or row_index >= len(wrapper.rows):
                    continue
                row = wrapper.rows[row_index]
                for cell_payload in row_payload.get("cells") or []:
                    cell_index = cell_payload.get("cellIndex")
                    if cell_index is None or cell_index >= len(row.cells):
                        continue
                    cell = row.cells[cell_index]
                    if cell.paragraphs:
                        _set_paragraph_text(cell.paragraphs[0], cell_payload.get("text") or "")
                field_key = row_payload.get("repeatingField")
                if field_key and field_key in _FIELD_BY_KEY[document_type]:
                    repeating_row = row
                    repeating_row_field = _FIELD_BY_KEY[document_type][field_key]

    if repeating_paragraph is not None and repeating_paragraph_field is not None:
        loop_var = repeating_paragraph_field["loopVar"]
        list_key = repeating_paragraph_field["key"]
        repeating_paragraph._p.addprevious(_marker_paragraph_element(f"{{%p for {loop_var} in {list_key} %}}"))
        repeating_paragraph._p.addnext(_marker_paragraph_element("{%p endfor %}"))

    if repeating_row is not None and repeating_row_field is not None:
        loop_var = repeating_row_field["loopVar"]
        list_key = repeating_row_field["key"]
        repeating_row._tr.addprevious(_clone_marker_row(repeating_row, f"{{%tr for {loop_var} in {list_key} %}}"))
        repeating_row._tr.addnext(_clone_marker_row(repeating_row, "{%tr endfor %}"))

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _sample_context(document_type: str) -> dict:
    """A minimal but structurally-complete context (one sample row/term)
    for every field in the catalog -- used only to validate a mapping
    renders cleanly (see save_mapping) before it's allowed to overwrite
    the template's actual file. Not used for a real document -- that's
    render_quotation_document/render_contract_document, with the
    project's real data."""
    context: dict = {}
    for field in MERGE_FIELD_CATALOG[document_type]:
        if field["kind"] == "text":
            context[field["key"]] = "Sample"
        elif field["kind"] == "repeating_table":
            context[field["key"]] = [{column["key"]: "Sample" for column in field["columns"]}]
        elif field["kind"] == "repeating_list":
            context[field["key"]] = ["Sample"]
    return context


def save_mapping(db: Session, template_id: int, blocks: list[dict], actor_id: int) -> DocumentTemplate:
    template = get_template(db, template_id)
    new_bytes = apply_mapping(template.storage_key, template.document_type, blocks)

    # Fail the save, not the next real download -- catches a stray
    # {{ / {% left over from a bad edit, or two locations flagged for
    # the same repeating field, immediately, with the template's
    # previous, still-working file left untouched on disk either way.
    try:
        DocxTemplate(io.BytesIO(new_bytes)).render(_sample_context(template.document_type))
    except Exception as exc:
        raise ValidationAppError(
            f"This field mapping couldn't be validated -- check for overlapping or malformed placeholders. ({exc})"
        ) from exc

    resolve_path(template.storage_key).write_bytes(new_bytes)
    template.file_size_bytes = len(new_bytes)
    audit_service.log_event(db, ENTITY_TYPE, template.id, f"{template.document_type} template fields mapped", actor_id)
    db.commit()
    db.refresh(template)
    return template
