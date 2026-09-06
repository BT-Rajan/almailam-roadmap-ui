"""Administration-level mailbox configuration used to send Quotation/
Contract documents. Only one row ever exists in practice -- `_row`
below always returns/creates id=1's row rather than supporting a list,
which is deliberate: one sending account for the whole firm, not a
per-user mailbox.

The SMTP_* environment variables (see core/config.py) remain a
fallback that takes priority over this row when set -- see
email_service._resolve_smtp_config, which is the single place that
decides which of the two actually gets used to send.
"""

import smtplib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret
from app.models.email_settings import EmailSettings
from app.services import audit_service

ENTITY_TYPE = "EMAIL_SETTINGS"

# Known-host presets, keyed by provider id -- the frontend shows these
# as picker options and fills the host/port fields on selection;
# "custom" leaves them for the admin to type. Values are the standard
# published SMTP server settings for each provider as of this writing.
PROVIDER_PRESETS: dict[str, dict] = {
    "gmail": {
        "label": "Gmail",
        "smtp_host": "smtp.gmail.com", "smtp_port": 587, "smtp_use_tls": True,
        "note": "Use a Google App Password, not your normal login password (requires 2-Step Verification).",
    },
    "outlook": {
        "label": "Outlook / Microsoft 365",
        "smtp_host": "smtp.office365.com", "smtp_port": 587, "smtp_use_tls": True,
        "note": "",
    },
    "yahoo": {
        "label": "Yahoo Mail",
        "smtp_host": "smtp.mail.yahoo.com", "smtp_port": 587, "smtp_use_tls": True,
        "note": "Requires a Yahoo App Password.",
    },
    "icloud": {
        "label": "iCloud Mail",
        "smtp_host": "smtp.mail.me.com", "smtp_port": 587, "smtp_use_tls": True,
        "note": "Requires an iCloud app-specific password.",
    },
    "custom": {
        "label": "Custom / other",
        "smtp_host": "", "smtp_port": 587, "smtp_use_tls": True,
        "note": "",
    },
}


def _row(db: Session) -> EmailSettings:
    row = db.query(EmailSettings).filter(EmailSettings.id == 1).first()
    if row is None:
        preset = PROVIDER_PRESETS["gmail"]
        row = EmailSettings(
            id=1, provider="gmail",
            smtp_host=preset["smtp_host"], smtp_port=preset["smtp_port"], smtp_use_tls=preset["smtp_use_tls"],
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get(db: Session) -> EmailSettings:
    return _row(db)


def update(db: Session, data: dict, user_id: int) -> EmailSettings:
    row = _row(db)
    audit_service.log_event(
        db, ENTITY_TYPE, row.id, "Email settings updated", user_id,
        previous_value=row.smtp_host, new_value=data["smtp_host"],
    )

    provider = data["provider"]
    preset = PROVIDER_PRESETS.get(provider)
    # For a known provider (anything but "custom"), host/port/encryption
    # are fixed published values, not something the admin form should be
    # able to drift away from -- enforced here too, not just disabled in
    # the UI, since a stale saved row (or any other caller of this
    # function) could otherwise carry the wrong host/port for the
    # provider it claims to be, which shows up as "the password doesn't
    # work" when the real problem is a wrong host or port.
    if preset and provider != "custom":
        row.smtp_host = preset["smtp_host"]
        row.smtp_port = preset["smtp_port"]
        row.smtp_use_tls = preset["smtp_use_tls"]
    else:
        row.smtp_host = data["smtp_host"]
        row.smtp_port = data["smtp_port"]
        row.smtp_use_tls = data["smtp_use_tls"]

    row.provider = provider
    row.username = data["username"]
    row.from_email = data["from_email"]
    row.from_name = data["from_name"]
    row.is_active = data["is_active"]

    password = data.get("password")
    if password is not None:
        row.password_encrypted = encrypt_secret(password) if password else None

    # Config changed -- the last test result no longer speaks to the
    # current settings, so don't leave a stale "OK" showing.
    row.last_tested_at = None
    row.last_test_ok = None
    row.last_test_error = None

    db.commit()
    db.refresh(row)
    return row


def get_smtp_credentials(db: Session) -> dict | None:
    """The saved mailbox's SMTP half, for email_service.py to send
    Quotation/Contract documents through when the server has no .env
    SMTP_* override configured. None if the mailbox isn't usable for
    sending yet (no host, or no password saved)."""
    row = _row(db)
    if not row.is_active or not row.smtp_host or not row.password_encrypted:
        return None
    password = decrypt_secret(row.password_encrypted)
    if not password:
        return None
    return {
        "host": row.smtp_host,
        "port": row.smtp_port,
        "use_tls": row.smtp_use_tls,
        "username": row.username or row.from_email,
        "password": password,
        "from_email": row.from_email,
        "from_name": row.from_name,
    }


def test_connection(db: Session) -> dict:
    """Opens (and immediately closes) a real SMTP connection with the
    saved settings. Never raises -- failures come back as
    {"ok": False, "message": ...} so the API layer doesn't need to
    special-case smtplib's own exception types, and the UI can show
    the result inline either way.
    """
    row = _row(db)
    if not row.smtp_host:
        return _record_test(db, row, False, "Enter an SMTP host first.")
    if not row.password_encrypted:
        return _record_test(db, row, False, "Set a mailbox password before testing the connection.")

    username = row.username or row.from_email
    # decrypt_secret never raises -- it returns "" if JWT_SECRET_KEY
    # changed since the password was saved, which must be treated the
    # same as no password being configured, not as an empty password.
    password = decrypt_secret(row.password_encrypted)
    if not password:
        return _record_test(db, row, False, "Stored password could not be decrypted (server key changed?). Re-enter it.")

    try:
        with smtplib.SMTP(row.smtp_host, row.smtp_port, timeout=15) as server:
            if row.smtp_use_tls:
                server.starttls()
            if username:
                server.login(username, password)
    except smtplib.SMTPNotSupportedError as exc:
        # Almost always means AUTH was attempted over a connection the
        # server never upgraded to TLS -- the standard symptom of
        # Encryption being set to "None" for this host/port.
        return _record_test(
            db, row, False,
            f"SMTP failed: {exc} Check that Encryption is set to STARTTLS "
            "(or SSL/TLS, matching the port), not None.",
        )
    except smtplib.SMTPAuthenticationError as exc:
        # The password is rejected, not the connection -- host/port/TLS
        # all worked. By far the most common cause for Gmail/Yahoo/
        # iCloud is using the normal account password instead of a
        # provider-issued app password (these providers reject regular
        # passwords for SMTP outright once 2-factor auth is on, even
        # though the same password logs into webmail fine).
        hint = (
            " Gmail, Yahoo, and iCloud all require a separate app password for SMTP -- "
            "your regular account password will be rejected here even if it's correct."
            if row.provider in ("gmail", "yahoo", "icloud") else ""
        )
        return _record_test(db, row, False, f"Authentication failed: {exc.smtp_error.decode(errors='replace')}{hint}")
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        return _record_test(db, row, False, f"SMTP connection failed: {exc}")

    return _record_test(db, row, True, "Connected successfully.")


def _record_test(db: Session, row: EmailSettings, ok: bool, message: str) -> dict:
    row.last_tested_at = datetime.now(timezone.utc)
    row.last_test_ok = ok
    row.last_test_error = None if ok else message
    db.commit()
    return {"ok": ok, "message": message}
