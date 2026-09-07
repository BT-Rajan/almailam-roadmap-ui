"""Sends a generated document (Quotation/Contract PDF) as an email
attachment -- the third leg of "download, print, and email should all
use this template" alongside document_template_service's document/PDF
renders.

Credentials come from .env (SMTP_* in core/config.py) when SMTP_HOST is
set -- infrastructure-level configuration, for a dedicated sending
account, same one-time deploy concern as the LLM provider keys -- and
otherwise fall back to the mailbox saved under Administration -> Email
(see email_settings_service.get_smtp_credentials), so an admin who'd
rather configure and test a mailbox from the UI doesn't need server
access to enable this at all. .env just lets that be overridden
without touching the database, matching the same override precedence
used for AI provider keys (see app.services.ai_service).
"""

import smtplib
from email.message import EmailMessage
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.exceptions import ValidationAppError
from app.services import email_settings_service


def _resolve_smtp_config(db: Session) -> dict | None:
    settings = get_settings()
    if settings.smtp_configured:
        return {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "use_tls": settings.SMTP_USE_TLS,
            "username": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD,
            "from_email": settings.smtp_from_address,
            "from_name": "",
        }
    return email_settings_service.get_smtp_credentials(db)


def is_configured(db: Session | None = None) -> bool:
    """Whether a real send would succeed right now -- an env override,
    or a saved-and-tested mailbox. Opens its own session when the
    caller doesn't already have one (e.g. a UI hint outside a request)."""
    if db is not None:
        return _resolve_smtp_config(db) is not None
    session = SessionLocal()
    try:
        return _resolve_smtp_config(session) is not None
    finally:
        session.close()


def send_email(to_email: str, subject: str, body_text: str, db: Optional[Session] = None) -> None:
    """Plain-text send, no attachment -- OTP codes and the onboarding
    welcome email (see client_service.py) use this directly;
    send_document_email below is a thin wrapper adding an attachment on
    top of the exact same SMTP/error-handling scaffolding."""
    owns_session = db is None
    session = db or SessionLocal()
    try:
        _send(session, to_email, subject, body_text, attachment=None)
    finally:
        if owns_session:
            session.close()


def send_document_email(
    to_email: str, subject: str, body_text: str,
    attachment_bytes: bytes, attachment_filename: str, attachment_mimetype: str,
    db: Optional[Session] = None,
) -> None:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        _send(
            session, to_email, subject, body_text,
            attachment=(attachment_bytes, attachment_filename, attachment_mimetype),
        )
    finally:
        if owns_session:
            session.close()


def _send(
    session: Session, to_email: str, subject: str, body_text: str,
    attachment: Optional[tuple[bytes, str, str]],
) -> None:
    config = _resolve_smtp_config(session)
    if config is None:
        raise ValidationAppError(
            "Email isn't configured on this server yet. Set SMTP_HOST (and the other SMTP_* "
            "variables) in the backend's environment, or save and test a mailbox under "
            "Administration -> Email."
        )

    from_display = f"{config['from_name']} <{config['from_email']}>" if config["from_name"] else config["from_email"]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_display
    message["To"] = to_email
    # Distinct per send -- RFC 5322 recommends a Message-ID, and its
    # absence is a common, easy-to-miss reason a receiving mail
    # server spam-scores or silently drops an otherwise legitimate
    # message.
    message["Message-ID"] = f"<{uuid4().hex}@{(config['from_email'] or '').rsplit('@', 1)[-1] or 'localhost'}>"
    message.set_content(body_text)

    if attachment is not None:
        attachment_bytes, attachment_filename, attachment_mimetype = attachment
        maintype, _, subtype = attachment_mimetype.partition("/")
        message.add_attachment(
            attachment_bytes, maintype=maintype, subtype=subtype or "octet-stream", filename=attachment_filename,
        )

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=30) as server:
            if config["use_tls"]:
                server.starttls()
            if config["username"]:
                server.login(config["username"], config["password"])
            server.send_message(message)
    except smtplib.SMTPNotSupportedError as exc:
        # Almost always means AUTH was attempted over a connection
        # the server never upgraded to TLS -- most servers only
        # advertise AUTH after STARTTLS, so this is the standard
        # symptom of Encryption being set to "None" (or the wrong
        # port for it).
        raise ValidationAppError(
            f"Failed to send email: {exc} This usually means the mailbox's SMTP Encryption is "
            "set to \"None\" -- set it to STARTTLS (or SSL/TLS, matching the port) under "
            "Administration -> Email and save."
        ) from exc
    except smtplib.SMTPAuthenticationError as exc:
        hint = (
            " Gmail, Yahoo, and iCloud all require a separate app password for SMTP -- "
            "your regular account password will be rejected here even if it's correct."
            if config.get("from_email", "").split("@")[-1] in ("gmail.com", "yahoo.com", "icloud.com", "me.com") else ""
        )
        raise ValidationAppError(
            f"Failed to send email: authentication failed -- {exc.smtp_error.decode(errors='replace')}{hint}"
        ) from exc
    except (OSError, smtplib.SMTPException) as exc:
        raise ValidationAppError(f"Failed to send email: {exc}") from exc
