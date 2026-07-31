from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the first ServiceOS admin user.")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--full-name", default="Administrator")
    return parser.parse_args()


def read_password() -> str:
    while True:
        password = getpass.getpass("Admin password (min 8 chars): ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords did not match, try again.")
            continue
        return password


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == args.username).first()
        if existing is not None:
            print(f"[skip] User '{args.username}' already exists.")
            return

        password = read_password()
        db.add(
            User(
                username=args.username,
                email=args.email,
                password_hash=hash_password(password),
                full_name=args.full_name,
                role="admin",
                is_active=True,
            )
        )
        db.commit()
        print(f"[ok] Created admin user '{args.username}'.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
