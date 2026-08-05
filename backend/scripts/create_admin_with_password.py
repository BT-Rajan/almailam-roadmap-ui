from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402


def create_admin_user(username: str, email: str, full_name: str, password: str) -> None:
    """Create an admin user with the provided password."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing is not None:
            print(f"[info] User '{username}' already exists. Skipping creation.")
            return

        # Create the admin user
        admin_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="Administrator",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        print(f"[success] Created admin user '{username}' with email '{email}'.")
    except Exception as e:
        db.rollback()
        print(f"[error] Failed to create admin user: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Create admin user with hardcoded password "Admin#99"
    create_admin_user(
        username="admin",
        email="admin@serviceos.local",
        full_name="System Administrator",
        password="Admin#99",
    )
