"""Checks that the database has every table and column the code uses.

install.sh runs this before restarting the API. schema.sql is only loaded
into an empty database, so a column added to the code later never reaches
an existing one by itself -- and the API then fails on every request that
touches that table. Stopping the deploy here keeps the running version up
and names exactly what's missing.

Only presence is checked: extra tables/columns in the database, types and
indexes are not (an index missing only costs speed).

    python -m scripts.check_schema        exit 0 = matches, 1 = something missing
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

import app.main  # noqa: E402,F401 -- registers every model on Base.metadata
from app.core.database import Base, engine  # noqa: E402


def missing_schema(bind: Engine) -> list[str]:
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    missing: list[str] = []
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            missing.append(f"table {table.name}")
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        missing += [f"column {table.name}.{column.name}" for column in table.columns if column.name not in existing_columns]
    return missing


def main() -> int:
    missing = missing_schema(engine)
    if not missing:
        print("[ok] Database has every table and column the code uses.")
        return 0
    print("[error] The database is missing what this version of the code needs:")
    for item in missing:
        print(f"  - {item}")
    print("Add them (see backend/schema.sql for the definitions), then re-run install.sh.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
