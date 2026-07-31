"""Claims the next number for a document type, atomically and race-free,
using SELECT ... FOR UPDATE inside the caller's own transaction -- the
caller commits (alongside whatever row it's creating with this number),
this function never commits on its own.

Format matches the frontend's real convention exactly (see
src/mock/quotations.ts, contracts.ts, governmentSubmissions.ts):
PREFIX-YEAR-### with the counter resetting to 1 every calendar year,
not jdk_clean's flat ever-incrementing PREFIX-##### (no year, never
resets) -- that's a genuinely different numbering scheme, so this is
adapted rather than ported as-is.

Note: Payment has no generated number of its own -- `referenceNumber`
on a Payment is an optional, user-supplied external reference (e.g. a
bank transfer ref), not something we generate. So there is no
'payment receipt' entry here despite the original B05 pass description
assuming one; only the three document types that actually have a
generated number in the real data model are configured below.
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import AppError

# doc_type -> (prefix, zero-padding width)
DOC_TYPE_CONFIG: dict[str, tuple[str, int]] = {
    "QUOTATION": ("QUO", 3),
    "CONTRACT": ("CON", 3),
    "GOVERNMENT_SUBMISSION": ("SUB", 3),
}


def next_number(db: Session, doc_type: str, year: int | None = None) -> str:
    if doc_type not in DOC_TYPE_CONFIG:
        raise AppError(f"No number series configured for '{doc_type}'.")
    prefix, padding = DOC_TYPE_CONFIG[doc_type]
    year = year or datetime.now(timezone.utc).year

    # Ensure this (doc_type, year) row exists without disturbing an
    # existing counter -- a harmless no-op update on conflict.
    db.execute(
        text(
            "INSERT INTO number_series (doc_type, year, prefix, next_number, padding) "
            "VALUES (:doc_type, :year, :prefix, 1, :padding) "
            "ON DUPLICATE KEY UPDATE doc_type = doc_type"
        ),
        {"doc_type": doc_type, "year": year, "prefix": prefix, "padding": padding},
    )

    row = db.execute(
        text(
            "SELECT next_number FROM number_series "
            "WHERE doc_type = :doc_type AND year = :year FOR UPDATE"
        ),
        {"doc_type": doc_type, "year": year},
    ).first()
    current = row.next_number

    db.execute(
        text(
            "UPDATE number_series SET next_number = next_number + 1 "
            "WHERE doc_type = :doc_type AND year = :year"
        ),
        {"doc_type": doc_type, "year": year},
    )

    return f"{prefix}-{year}-{str(current).zfill(padding)}"
