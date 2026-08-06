import secrets
import string
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit_service

ENTITY_TYPE = "USER"
TEMP_PASSWORD_LENGTH = 14


def _derive_username(db: Session, email: str) -> str:
    base = "".join(ch for ch in email.split("@")[0].lower() if ch.isalnum() or ch in ".-_")
    base = base or "user"
    candidate = base
    suffix = 1
    while db.query(User).filter(User.username == candidate).first() is not None:
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def _generate_temporary_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(TEMP_PASSWORD_LENGTH))


def parse_user_id(raw: str) -> int:
    text = raw.removeprefix("USR-") if raw.upper().startswith("USR-") else raw
    if not text.isdigit():
        raise ValidationAppError("Invalid user id.")
    return int(text)


def list_users(db: Session) -> list[User]:
    return db.query(User).filter(User.deleted_at.is_(None)).order_by(User.id.asc()).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise NotFoundError("User")
    return user


def create_user(db: Session, payload: UserCreate, actor_id: int) -> tuple[User, str]:
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise ConflictError("A user with this email already exists.")

    username = _derive_username(db, payload.email)
    temporary_password = _generate_temporary_password()

    user = User(
        username=username,
        email=payload.email,
        password_hash=hash_password(temporary_password),
        full_name=payload.name,
        designation=payload.designation,
        mobile=payload.mobile,
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    audit_service.log_event(
        db, ENTITY_TYPE, user.id, "User created", actor_id, new_value=user.role
    )
    db.commit()
    db.refresh(user)
    return user, temporary_password


def update_user(db: Session, user_id: int, payload: UserUpdate, actor_id: int) -> User:
    user = get_user(db, user_id)
    if payload.role is not None and payload.role != user.role:
        audit_service.log_event(
            db, ENTITY_TYPE, user.id, "Role changed", actor_id,
            previous_value=user.role, new_value=payload.role,
        )
    if payload.name is not None:
        user.full_name = payload.name
    if payload.designation is not None:
        user.designation = payload.designation
    if payload.mobile is not None:
        user.mobile = payload.mobile
    if payload.role is not None:
        user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


def set_user_status(db: Session, user_id: int, status: str, actor_id: int) -> User:
    user = get_user(db, user_id)
    previous_status = "Active" if user.is_active else "Inactive"
    if previous_status != status:
        audit_service.log_event(
            db, ENTITY_TYPE, user.id, "Status changed", actor_id,
            previous_value=previous_status, new_value=status,
        )
    user.is_active = status == "Active"
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, actor_id: int) -> None:
    if user_id == actor_id:
        raise ValidationAppError("You cannot delete your own account.")
    user = get_user(db, user_id)
    audit_service.log_event(db, ENTITY_TYPE, user.id, "User deleted", actor_id, previous_value=user.full_name)
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()
