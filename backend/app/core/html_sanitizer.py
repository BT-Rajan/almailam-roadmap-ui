"""Sanitizes the rich-text HTML saved from the Quotation/Contract preview
editors (scope summary, clauses, notes, terms). The editor itself only
ever produces bold/italic/underline, font-size spans, and inline (base64)
images, but a request can reach this API without going through that
editor, so the allowlist is enforced here too rather than trusting the
client-side DOMPurify pass alone.
"""

import nh3

_ALLOWED_TAGS = {"p", "br", "b", "strong", "i", "em", "u", "span", "ul", "ol", "li", "img"}
_ALLOWED_ATTRIBUTES = {"span": {"style"}, "img": {"src", "alt", "style"}}
_ALLOWED_STYLE_PROPERTIES = {"font-size"}
_ALLOWED_URL_SCHEMES = {"data", "http", "https"}


def sanitize_html(value: str | None) -> str | None:
    if value is None:
        return None
    return nh3.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        filter_style_properties=_ALLOWED_STYLE_PROPERTIES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel=None,
    )
