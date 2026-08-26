import base64
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

settings = get_settings()

BCRYPT_MAX_BYTES = 72


def _secret_fernet() -> Fernet:
    """Encryption key for at-rest secrets (currently: AIProviderConfig.
    api_key_encrypted) derived from JWT_SECRET_KEY rather than a second
    dedicated env var -- JWT_SECRET_KEY is already required for auth to
    work at all and is stable across restarts/redeploys, so this piggybacks
    on a secret every deployment already has instead of adding a new
    manual setup step."""
    digest = hashlib.sha256(f"ai-provider-key:{settings.JWT_SECRET_KEY}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(raw: str) -> str:
    return _secret_fernet().encrypt(raw.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Returns '' (never raises) if the token can't be decrypted -- e.g.
    JWT_SECRET_KEY changed since it was saved. Callers must treat that the
    same as no key being configured, not as an error to surface."""
    try:
        return _secret_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    subject: str, extra_claims: dict | None = None, expire_minutes: int | None = None
) -> str:
    now = datetime.now(timezone.utc)
    minutes = expire_minutes if expire_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at). The jti is persisted so the token can be revoked."""
    jti = str(uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "iat": now, "exp": expires_at, "type": "refresh", "jti": jti}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid or expired token") from exc
