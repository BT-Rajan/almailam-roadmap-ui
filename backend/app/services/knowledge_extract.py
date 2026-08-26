"""Plain-text extraction for uploaded knowledgebase documents.

Supports PDF, DOCX, and plain text. Extraction never raises for a bad
file -- it returns (text, ok, error_message) so the upload can still be
recorded (as a failed/empty source) rather than losing the user's upload
entirely; the caller decides what to do with a failed extraction.

Arabic text: pypdf and python-docx both read Unicode text runs directly
(no special handling needed for Arabic script itself), but this only
covers text-layer PDFs/DOCX -- a scanned/image-only PDF has no text layer
to extract and yields empty text. There is no OCR step in this pipeline.
"""

import io

import docx
import pypdf

from app.core.exceptions import ValidationAppError

KNOWLEDGE_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt"}

CONTENT_TYPE_BY_EXTENSION = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}


def content_type_for_extension(extension: str) -> str:
    content_type = CONTENT_TYPE_BY_EXTENSION.get(extension.lower())
    if not content_type:
        raise ValidationAppError(
            f"File type '{extension}' is not supported for the knowledgebase. "
            f"Allowed types: {', '.join(sorted(KNOWLEDGE_UPLOAD_EXTENSIONS))}"
        )
    return content_type


def extract_text(content_type: str, raw: bytes) -> tuple[str, bool, str]:
    """Returns (text, ok, error_message)."""
    try:
        if content_type == "pdf":
            reader = pypdf.PdfReader(io.BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(pages).strip()
        elif content_type == "docx":
            document = docx.Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in document.paragraphs).strip()
        elif content_type == "txt":
            text = raw.decode("utf-8", errors="replace").strip()
        else:
            return "", False, f"Unsupported content type '{content_type}'."
    except Exception as exc:  # noqa: BLE001 -- any parser failure is reported, not swallowed
        return "", False, f"Could not read this file: {exc}"

    if not text:
        return "", False, "No extractable text was found in this file (it may be a scanned/image-only document)."
    return text, True, ""


def cap_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True
