"""Sends a generated document (Quotation/Contract PDF) as an email
attachment -- the third leg of "download, print, and email should all
use this template" alongside document_template_service's document/PDF
renders. There is no in-app admin screen for mail server credentials
(see Settings.SMTP_* in core/config.py): this is infrastructure-level
.env configuration, same as the LLM provider keys, since it's a
one-time deploy concern, not something that changes per project.
"""

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


def send_document_email(
    to_email: str, subject: str, body_text: str,
    attachment_bytes: bytes, attachment_filename: str, attachment_mimetype: str,
) -> None:
    settings = get_settings()
    if not settings.smtp_configured:
        raise ValidationAppError(
            "Email is not configured on this server. Set SMTP_HOST and either SMTP_FROM_ADDRESS or "
            "SMTP_USERNAME in the backend's environment to enable it."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_address
    message["To"] = to_email
    message.set_content(body_text)

    maintype, _, subtype = attachment_mimetype.partition("/")
    message.add_attachment(
        attachment_bytes, maintype=maintype, subtype=subtype or "octet-stream", filename=attachment_filename,
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise ValidationAppError(f"Failed to send email: {exc}") from exc
