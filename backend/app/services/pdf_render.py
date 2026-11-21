"""Renders a GovernmentForm's {{token}} template into a real PDF or DOCX file.

Mirrors src/utils/governmentFormHelpers.ts's renderGovernmentFormTemplate
exactly (same {{token}} syntax, same placeholder for a missing value) so a
filled document looks identical to what the admin/staff already saw in the
client-side preview -- this is just the first place that turns it into an
actual, saved file instead of an on-screen-only render.

Uses WeasyPrint (HTML -> PDF) rather than a rasterized "print the page"
screenshot: these documents are legal agreements/undertakings that may be
printed and signed, so real, selectable, crisply-printable text matters.
WeasyPrint needs Pango/Cairo/GDK-Pixbuf shared libraries on the host (a
system dependency, not a pip package) -- see requirements.txt's comment.

Arabic text needs an explicit, bundled font: the container/server this
runs on is not guaranteed to have any Arabic-capable font installed via
fontconfig, and a silent fallback to a Latin-only font would render Arabic
as invisible boxes ("tofu") rather than raise an error. Noto Naskh Arabic
(SIL Open Font License, see assets/fonts/NotoNaskhArabic-OFL.txt) is
bundled here and referenced by an explicit file:// @font-face rule so
rendering is correct regardless of what's installed system-wide.

Layout follows the reference letters the engineering office issues to
Kuwait Municipality (A4, RTL, 12pt, date top-right, underlined centred
subject, justified body, dotted-leader field lines, bold closing line,
two-party signature row). The same parsed block list (letter_blocks)
drives both the PDF and the DOCX renderers, so the two outputs share their
spacing and alignment.
"""

import io
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from weasyprint import HTML

from app.core.exceptions import ValidationAppError

_TOKEN_RE = re.compile(r"{{\s*(\w+)\s*}}", re.UNICODE)
_MISSING_PLACEHOLDER = "………………"

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf"

# Letter geometry, taken from the reference letters (A4). Top is slightly
# tighter than the bottom because the letterhead sits above the date line.
PAGE_MARGIN_CM = {"top": 1.6, "right": 2.54, "bottom": 2.54, "left": 2.54}
# The reference letters are set in Univers Next Arabic. That font is not
# bundled, so the DOCX names it (Word uses it where installed) and the PDF
# uses the bundled Noto Naskh Arabic instead.
DOCX_FONT_NAME = "Univers Next Arabic"

# Line roles, matched on the start of each line (after stripping). Order in
# _line_role matters: a dotted field line like "السيد/ ......" is a field,
# not an addressee, so fields are checked before addressees.
_DATE_PREFIXES = ("التاريخ", "الكويت في", "Date")
_SUBJECT_PREFIXES = ("الموضوع", "Subject")
_ADDRESSEE_PREFIXES = ("السيد", "السادة", "Dear")
_SALUTATION_PREFIXES = ("تحية طيبة",)
_CLOSING_PREFIXES = ("وتفضلوا", "وهذا إقرار", "Yours")
_SIGNATURE_MARKERS = (("طرف أول", "طرف ثاني"), ("First Party", "Second Party"))
_FIELD_RE = re.compile(r"^[^.…:/]{1,40}?\s*[:/]\s*\S")
# Field lines are short "label: value" / "label / value" lines. Checked on the
# rendered text, so a filled value like "منطقة / السالمية" still counts.
_FIELD_MAX_LENGTH = 90
_MULTI_SPACE_RE = re.compile(r"\s{3,}")


def extract_tokens(template: str) -> list[str]:
    """Every distinct {{token}} in a template, in first-seen order --
    mirrors src/utils/governmentFormHelpers.ts's extractTemplateTokens
    exactly (same regex, same dedup-by-first-seen-order). Used by
    project_form_service.py to check a submission's field_values
    actually covers every token before generating the document, instead
    of silently rendering render_template's own dotted-line "missing
    value" placeholder into what may become a real, signed government
    submission."""
    seen: set[str] = set()
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(template):
        token = match.group(1)
        if token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def assert_field_values_complete(fields: list | None, template: str | None, field_values: dict[str, str]) -> None:
    """Every {{token}} in a form's template must have a real, non-blank
    value before this becomes a saved document or Project Document --
    shared by government_service.fill_form and
    project_form_service.create_project_form_entry/
    update_project_form_entry, the app's two places that turn a
    GovernmentForm template into a saved file. Previously neither
    checked this at all (frontend or backend), so a form could be
    "filled" and saved with every field left blank, silently rendering
    render_template's own dotted-line "missing value" placeholder into
    what may become a real, signed government submission.

    Raises ValidationAppError. `fields` is a GovernmentForm.fields JSON
    value (list of {"token", "label", ...} dicts, or None)."""
    field_labels = {f["token"]: f["label"] for f in (fields or [])}
    missing = [
        field_labels.get(token, token)
        for token in extract_tokens(template or "")
        if not (field_values.get(token) or "").strip()
    ]
    if missing:
        raise ValidationAppError(f"Please fill in: {', '.join(missing)}.")


def render_template(template: str, context: dict[str, str | None]) -> str:
    """Same substitution rule as the frontend's renderGovernmentFormTemplate:
    a token with a non-blank context value is replaced with it; anything
    else (missing key, empty string, whitespace-only) becomes a visible
    placeholder line rather than silently vanishing."""

    def _replace(match: re.Match[str]) -> str:
        value = context.get(match.group(1))
        return value if value and value.strip() else _MISSING_PLACEHOLDER

    return _TOKEN_RE.sub(_replace, template)


def _line_role(line: str) -> str:
    if line.startswith(_DATE_PREFIXES):
        return "date"
    if line.startswith(_SUBJECT_PREFIXES):
        return "subject"
    if any(first in line and second in line for first, second in _SIGNATURE_MARKERS) and _MULTI_SPACE_RE.search(line):
        return "signature"
    if line.startswith(_ADDRESSEE_PREFIXES):
        return "addressee"
    if line.startswith(_SALUTATION_PREFIXES):
        return "salutation"
    if line.startswith(_CLOSING_PREFIXES):
        return "closing"
    if len(line) <= _FIELD_MAX_LENGTH and _FIELD_RE.match(line):
        return "field"
    return "body"


def letter_blocks(body_text: str) -> list[tuple[str, str]]:
    """Splits a rendered body into (role, text) blocks in document order.

    Blank lines separate paragraphs, as the templates are authored. Within a
    paragraph, consecutive body lines stay one block (joined by line breaks),
    while every other line becomes its own block so it can take its own
    alignment and spacing -- a dotted field line, a subject, a closing."""
    blocks: list[tuple[str, str]] = []
    for paragraph in body_text.split("\n\n"):
        pending_body: list[str] = []
        for raw_line in paragraph.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            role = _line_role(line)
            if role == "body":
                pending_body.append(line)
                continue
            if pending_body:
                blocks.append(("body", "\n".join(pending_body)))
                pending_body = []
            blocks.append((role, line))
        if pending_body:
            blocks.append(("body", "\n".join(pending_body)))
    return blocks


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _block_html(role: str, text: str) -> str:
    if role == "signature":
        parts = [part.strip() for part in _MULTI_SPACE_RE.split(text) if part.strip()]
        cells = "".join(f"<span>{_escape_html(part)}</span>" for part in parts)
        return f'<div class="signature-row">{cells}</div>'
    body = _escape_html(text).replace("\n", "<br/>")
    return f'<p class="{role}">{body}</p>'


def render_agreement_pdf(title: str, body_text: str) -> bytes:
    """Renders a filled form into a print-ready PDF in the reference-letter
    layout (see module docstring). The title is shown as a heading only when
    the body has no subject line of its own, so letters don't carry a second
    title above their own "الموضوع" line."""
    blocks = letter_blocks(body_text)
    has_subject = any(role == "subject" for role, _ in blocks)
    title_html = "" if has_subject else f'<h1 class="title">{_escape_html(title)}</h1>'
    blocks_html = "".join(_block_html(role, text) for role, text in blocks)
    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'NotoNaskhArabic';
    src: url('file://{FONT_PATH}');
  }}
  @page {{
    size: A4;
    margin: {PAGE_MARGIN_CM["top"]}cm {PAGE_MARGIN_CM["right"]}cm {PAGE_MARGIN_CM["bottom"]}cm {PAGE_MARGIN_CM["left"]}cm;
  }}
  body {{
    font-family: 'NotoNaskhArabic', sans-serif;
    direction: rtl;
    text-align: right;
    font-size: 12pt;
    line-height: 1.6;
    color: #1a1a2e;
  }}
  h1.title {{ font-size: 14pt; text-align: center; font-weight: bold; margin: 0 0 1em; }}
  p {{ margin: 0 0 0.5em; }}
  p.date {{ margin-bottom: 0.9em; }}
  p.addressee {{ font-weight: bold; margin: 0; }}
  p.salutation {{ font-weight: bold; margin: 0.9em 0 1em; }}
  p.subject {{ text-align: center; font-weight: bold; text-decoration: underline; margin: 1em 0 1.2em; }}
  p.body {{ text-align: justify; margin-bottom: 0.9em; }}
  p.field {{ line-height: 2.1; margin: 0; }}
  p.closing {{ text-align: center; font-weight: bold; margin: 1.4em 0 1.6em; }}
  .signature-row {{ display: flex; justify-content: space-between; margin: 0.9em 0; }}
</style>
</head>
<body>
{title_html}
{blocks_html}
</body>
</html>"""
    return HTML(string=html).write_pdf()


def _docx_paragraph(container, role: str, text: str):
    paragraph = container.add_paragraph()
    # w:bidi has to come before spacing/alignment in the paragraph XML, so it
    # is added first; python-docx then inserts the later properties in order.
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_before = Pt(0)
    paragraph_format.space_after = Pt(0)
    if role == "body":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph_format.line_spacing = 1.5
        paragraph_format.space_after = Pt(9)
    elif role == "field":
        paragraph_format.line_spacing = 2.0
    elif role == "date":
        paragraph_format.space_after = Pt(9)
    elif role == "salutation":
        paragraph_format.space_before = Pt(9)
        paragraph_format.space_after = Pt(12)
    elif role == "subject":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph_format.space_before = Pt(12)
        paragraph_format.space_after = Pt(12)
    elif role == "closing":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph_format.space_before = Pt(14)
        paragraph_format.space_after = Pt(16)
    elif role == "title":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph_format.space_after = Pt(12)

    lines = text.split("\n")
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        run.bold = role in ("addressee", "salutation", "subject", "closing", "title")
        run.underline = role == "subject"
        if role == "title":
            run.font.size = Pt(14)
        if index < len(lines) - 1:
            run.add_break()
    return paragraph


def _docx_signature_row(document, text: str) -> None:
    parts = [part.strip() for part in _MULTI_SPACE_RE.split(text) if part.strip()]
    table = document.add_table(rows=1, cols=len(parts))
    for cell, part in zip(table.rows[0].cells, parts):
        cell_paragraph = cell.paragraphs[0]
        cell_paragraph._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
        run = cell_paragraph.add_run(part)
        run.bold = False


def render_agreement_docx(title: str, body_text: str) -> bytes:
    """The same letter layout as render_agreement_pdf, as an editable .docx:
    A4 with the reference letters' margins, right-to-left paragraphs, and the
    same block roles and spacing (see letter_blocks)."""
    document = Document()
    section = document.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(PAGE_MARGIN_CM["top"])
    section.bottom_margin = Cm(PAGE_MARGIN_CM["bottom"])
    section.left_margin = Cm(PAGE_MARGIN_CM["left"])
    section.right_margin = Cm(PAGE_MARGIN_CM["right"])

    normal = document.styles["Normal"]
    normal.font.name = DOCX_FONT_NAME
    normal.font.size = Pt(12)
    rpr_fonts = normal.element.get_or_add_rPr().get_or_add_rFonts()
    for attribute in ("w:ascii", "w:hAnsi", "w:cs"):
        rpr_fonts.set(qn(attribute), DOCX_FONT_NAME)

    blocks = letter_blocks(body_text)
    if not any(role == "subject" for role, _ in blocks):
        _docx_paragraph(document, "title", title)
    for role, text in blocks:
        if role == "signature":
            _docx_signature_row(document, text)
        else:
            _docx_paragraph(document, role, text)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
