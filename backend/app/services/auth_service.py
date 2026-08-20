from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AuthError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User

settings = get_settings()

GENERIC_LOGIN_ERROR = "Invalid username or password."


def _issue_tokens(db: Session, user: User) -> dict:
    access_token = create_access_token(str(user.id), {"role": user.role})
    refresh_token, jti, expires_at = create_refresh_token(str(user.id))

    db.add(
        RefreshToken(
            jti=jti,
            user_id=user.id,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def _is_locked(user: User) -> bool:
    if user.locked_until is None:
        return False
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return locked_until > datetime.now(timezone.utc)


def _register_failed_attempt(db: Session, user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=settings.LOCKOUT_MINUTES
        )
    db.commit()


def login(db: Session, username: str, password: str) -> dict:
    user = (
        db.query(User)
        .filter(User.username == username, User.deleted_at.is_(None))
        .first()
    )
    return _authenticate_and_issue_tokens(db, user, password)


def login_with_employee_id(db: Session, employee_id: str, password: str) -> dict:
    """Site Engineer Portal's login (see api/site_portal.py) -- same
    accounts, same password_hash, same lockout/security behaviour as the
    staff username login above, just resolved by employee_id instead.
    Deliberately the same generic error message either way, for the
    same reason: this can't be used to enumerate valid employee IDs
    either."""
    user = (
        db.query(User)
        .filter(User.employee_id == employee_id, User.deleted_at.is_(None))
        .first()
    )
    return _authenticate_and_issue_tokens(db, user, password)


def _authenticate_and_issue_tokens(db: Session, user: User | None, password: str) -> dict:
    # Same generic message whether the account doesn't exist or the
    # password is wrong -- never confirms which, so this can't be used to
    # enumerate valid usernames/employee IDs.
    if user is None:
        raise AuthError(GENERIC_LOGIN_ERROR)

    if not user.is_active:
        raise AuthError("This account has been deactivated.")

    if _is_locked(user):
        raise AuthError(
            f"Too many failed attempts. Try again in {settings.LOCKOUT_MINUTES} minutes."
        )

    if not verify_password(password, user.password_hash):
        _register_failed_attempt(db, user)
        raise AuthError(GENERIC_LOGIN_ERROR)

    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    return _issue_tokens(db, user)


def refresh(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise AuthError("Invalid or expired refresh token.") from exc

    if payload.get("type") != "refresh":
        raise AuthError("Invalid token type.")

    jti = payload.get("jti")
    record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if record is None or record.revoked:
        raise AuthError("This session has been revoked. Please log in again.")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise AuthError("Session expired. Please log in again.")

    user = (
        db.query(User)
        .filter(User.id == int(payload["sub"]), User.deleted_at.is_(None))
        .first()
    )
    if user is None or not user.is_active:
        raise AuthError("Account is no longer active.")

    # Rotate: revoke the used refresh token and issue a new pair, so a
    # captured token can only be replayed once before it stops working.
    record.revoked = True
    db.commit()
    return _issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        return
    jti = payload.get("jti")
    if not jti:
        return
    record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if record is not None:
        record.revoked = True
        db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise ValidationAppError("Current password is incorrect.")
    user.password_hash = hash_password(new_password)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)
    ).update({"revoked": True})
    db.commit()
