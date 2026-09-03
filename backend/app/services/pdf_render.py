"""Renders a GovernmentForm's {{token}} template into a real PDF file.

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
"""

import re
from pathlib import Path

from weasyprint import HTML

_TOKEN_RE = re.compile(r"{{\s*(\w+)\s*}}", re.UNICODE)
_MISSING_PLACEHOLDER = "………………"

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf"


def render_template(template: str, context: dict[str, str | None]) -> str:
    """Same substitution rule as the frontend's renderGovernmentFormTemplate:
    a token with a non-blank context value is replaced with it; anything
    else (missing key, empty string, whitespace-only) becomes a visible
    placeholder line rather than silently vanishing."""

    def _replace(match: re.Match[str]) -> str:
        value = context.get(match.group(1))
        return value if value and value.strip() else _MISSING_PLACEHOLDER

    return _TOKEN_RE.sub(_replace, template)


def _paragraphs_html(body_text: str) -> str:
    """Blank-line-separated paragraphs, single newlines within a paragraph
    become <br> -- matches how the template text is authored (see
    standardGovernmentForms.ts's seed templates) and how the client-side
    preview already displays it (a whitespace-pre-wrap <pre> block)."""
    paragraphs = [p for p in body_text.split("\n\n")]
    return "".join(
        f"<p>{_escape_html(paragraph).replace(chr(10), '<br/>')}</p>"
        for paragraph in paragraphs
        if paragraph.strip()
    )


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_agreement_pdf(title: str, body_text: str) -> bytes:
    """Renders a filled form's title + merged body into a print-ready PDF,
    RTL by default (every template in this app so far is Arabic or
    Arabic-primary bilingual; direction is a document-wide CSS property
    here, not per-run, since WeasyPrint has no live language detection)."""
    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'NotoNaskhArabic';
    src: url('file://{FONT_PATH}');
  }}
  @page {{ size: A4; margin: 2.5cm 2cm; }}
  body {{
    font-family: 'NotoNaskhArabic', sans-serif;
    direction: rtl;
    text-align: right;
    font-size: 13pt;
    line-height: 1.9;
    color: #1a1a2e;
  }}
  h1 {{
    font-size: 16pt;
    text-align: center;
    margin: 0 0 1.5em;
  }}
  p {{ margin: 0 0 1em; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>{_escape_html(title)}</h1>
{_paragraphs_html(body_text)}
</body>
</html>"""
    return HTML(string=html).write_pdf()
