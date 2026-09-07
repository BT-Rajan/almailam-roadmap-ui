"""Shared mechanics for any workflow step gated behind a client reading
back a one-time email code -- client onboarding (client_service.
send_onboarding_otp/verify_onboarding_otp), project Requirement
confirmation (project_service.send_requirement_otp/verify_requirement_otp),
and quotation approval (quotation_service.send_quotation_otp/
verify_quotation_otp) all use this. Each caller stores its own
otp_code_hash/otp_expires_at/otp_attempts/otp_sent_at columns (see
EmailOtpMixin in app/models/mixins.py) since they live on different rows
of different tables, but the generation/hashing/expiry/attempt-limit
logic is identical and lives here once instead of being reimplemented
per caller.
"""

import secrets
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password, verify_password

CODE_LENGTH = 6
VALIDITY_MINUTES = 24 * 60
MAX_ATTEMPTS = 5


def generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(CODE_LENGTH))


def hash_code(code: str) -> str:
    # bcrypt, same primitive as User.password_hash -- no second hashing
    # scheme just for a 6-digit code.
    return hash_password(code)


def code_matches(code: str, code_hash: str | None) -> bool:
    if not code_hash:
        return False
    return verify_password(code.strip(), code_hash)


def new_expiry() -> datetime:
    # Naive UTC, matching every other DateTime column/comparison in this
    # app (see e.g. client_service.check_and_notify_stale_onboarding) --
    # MySQL DATETIME strips tzinfo on storage anyway.
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=VALIDITY_MINUTES)


def is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    return datetime.now(timezone.utc).replace(tzinfo=None) > expires_at


def validity_label() -> str:
    """Human-readable form of VALIDITY_MINUTES for OTP email bodies --
    e.g. "24 hours" rather than the literal "1440 minutes". Falls back
    to a minutes phrasing if VALIDITY_MINUTES is ever set below an hour."""
    if VALIDITY_MINUTES % 60 == 0:
        hours = VALIDITY_MINUTES // 60
        return f"{hours} hour" + ("" if hours == 1 else "s")
    return f"{VALIDITY_MINUTES} minutes"
