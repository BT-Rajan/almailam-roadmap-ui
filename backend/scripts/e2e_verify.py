"""DB-side helper for the e2e-workflow test stream (e2e-workflow/ at the
repo root -- see e2e-workflow/README.md).

This is intentionally separate from the app's normal request path: the
Playwright specs drive the real UI/API to create data, then shell out to
this script to read back exactly what landed in the database so the
"sent vs saved" comparison is against the actual DB row, not against
another layer of the same API that wrote it.

Two jobs, both scoped strictly to the IDs the tests themselves created
(never a table-wide query, never anything resembling real/production
data):

    dump   <entity> <id>   -- print one row as JSON (DB column values,
                               using the model's actual Python types --
                               dates/Decimals are stringified so the
                               output is plain JSON).
    cleanup <state-file>    -- delete everything the run created, in the
                               dependency order the schema's FKs require
                               (see e2e-workflow/README.md), then confirm
                               nothing under those IDs remains. Safe to
                               call on a state file where some IDs were
                               never filled in (a run that failed
                               partway through) -- each step is skipped
                               if its ID is missing.

Run from backend/ with the same environment (.env, venv) the app itself
uses, e.g.:

    python -m scripts.e2e_verify dump client 123
    python -m scripts.e2e_verify cleanup ../e2e-workflow/.artifacts/state.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.client import Client, ClientAddress, ClientContact, ClientIdentification  # noqa: E402
from app.models.contract import Contract  # noqa: E402
from app.models.payment import Adjustment, FinancialAgreement, Payment, Refund  # noqa: E402
from app.models.project import Project, ProjectSelectedActivity  # noqa: E402
from app.models.quotation import Quotation  # noqa: E402


def _jsonable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def row_to_dict(obj) -> dict:
    mapper = inspect(obj).mapper
    return {col.key: _jsonable(getattr(obj, col.key)) for col in mapper.column_attrs}


ENTITY_MODELS = {
    "client": Client,
    "project": Project,
    "quotation": Quotation,
    "contract": Contract,
    "agreement": FinancialAgreement,
}

# How each entity's identifier maps to a row. Deliberately NOT a single
# shared "try numeric PK, then fall back to a business key" heuristic:
# project_no/quotation_no/contract_no (e.g. "PRJ-2026-0007") end in
# digits too, and a generic trailing-digits regex extracting "7" and
# trying db.get(Project, 7) first could silently match an unrelated
# REAL project with that PK before ever reaching the correct
# project_no lookup below -- exactly the "touched an existing record"
# failure this whole stream exists to prevent. So each entity uses only
# the one lookup that's actually correct for the identifier its own
# API returns:
#   client, agreement  -- caller always has a numeric-ish ID (a client
#                          ID straight from the URL; the FA-{id:03d}
#                          formatted string schemas/payment.py returns
#                          for a Financial Agreement, since it has no
#                          business-key column of its own).
#   project/quotation/contract -- caller always has the business number
#                          itself (it *is* the API's own `id` field).
NUMERIC_ENTITIES = {"client", "agreement"}
LOOKUP_FIELDS = {
    "project": "project_no",
    "quotation": "quotation_no",
    "contract": "contract_no",
}


def _resolve_pk(identifier: str) -> int | None:
    """Only for NUMERIC_ENTITIES. Accepts a plain numeric ID or a
    formatted "FA-007" style string (FinancialAgreementOut.id --
    schemas/payment.py -- has no business-key column to look up by)."""
    if identifier.isdigit():
        return int(identifier)
    match = re.fullmatch(r"[A-Za-z]+-0*(\d+)", identifier)
    return int(match.group(1)) if match else None


def dump(db: Session, entity: str, identifier: str) -> dict:
    model = ENTITY_MODELS[entity]
    obj = None
    if entity in NUMERIC_ENTITIES:
        pk = _resolve_pk(identifier)
        obj = db.get(model, pk) if pk is not None else None
    else:
        obj = db.query(model).filter(getattr(model, LOOKUP_FIELDS[entity]).__eq__(identifier)).first()
    if obj is None:
        raise SystemExit(f"No {entity} found for '{identifier}'")
    data = row_to_dict(obj)
    if entity == "client":
        data["contacts"] = [
            row_to_dict(c) for c in db.query(ClientContact).filter(ClientContact.client_id == obj.id).all()
        ]
        data["addresses"] = [
            row_to_dict(a) for a in db.query(ClientAddress).filter(ClientAddress.client_id == obj.id).all()
        ]
        data["identifications"] = [
            row_to_dict(i)
            for i in db.query(ClientIdentification).filter(ClientIdentification.client_id == obj.id).all()
        ]
    if entity == "project":
        data["selectedActivities"] = [
            row_to_dict(a)
            for a in db.query(ProjectSelectedActivity).filter(ProjectSelectedActivity.project_id == obj.id).all()
        ]
    return data


def cleanup(db: Session, state: dict) -> dict:
    """Deletes, in strict FK-dependency order, only the rows whose IDs
    are present in `state`. Returns a report of what was actually
    removed so the calling test can assert cleanup really happened
    rather than silently no-op'ing.
    """
    removed: dict[str, bool] = {}

    def _delete(model, id_key: str, label: str) -> None:
        raw_id = state.get(id_key)
        removed[label] = False
        if not raw_id:
            return
        if label in NUMERIC_ENTITIES:
            pk = _resolve_pk(str(raw_id))
            obj = db.get(model, pk) if pk is not None else None
        else:
            obj = db.query(model).filter(getattr(model, LOOKUP_FIELDS[label]).__eq__(raw_id)).first()
        if obj is not None:
            db.delete(obj)
            db.flush()
            removed[label] = True

    # Deepest children of financial_agreements first (RESTRICT FKs) --
    # payment_obligations itself CASCADEs off the agreement, so it's not
    # deleted explicitly.
    for payment_id in state.get("paymentIds", []):
        obj = db.get(Payment, int(payment_id))
        if obj is not None:
            db.delete(obj)
    for refund_id in state.get("refundIds", []):
        obj = db.get(Refund, int(refund_id))
        if obj is not None:
            db.delete(obj)
    for adjustment_id in state.get("adjustmentIds", []):
        obj = db.get(Adjustment, int(adjustment_id))
        if obj is not None:
            db.delete(obj)
    db.flush()

    _delete(FinancialAgreement, "agreementId", "agreement")
    # Contract before Quotation (contracts.quotation_id is RESTRICT).
    _delete(Contract, "contractNo", "contract")
    _delete(Quotation, "quotationNo", "quotation")
    # Project before Client (projects.client_id is RESTRICT). Project's
    # own children (selected activities/permits, scope revisions,
    # timeline events, handover checklist) all CASCADE off project_id.
    _delete(Project, "projectNo", "project")
    _delete(Client, "clientId", "client")

    db.commit()
    return removed


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    command = sys.argv[1]
    db = SessionLocal()
    try:
        if command == "dump":
            entity, identifier = sys.argv[2], sys.argv[3]
            print(json.dumps(dump(db, entity, identifier), indent=2, default=_jsonable))
        elif command == "cleanup":
            state_path = Path(sys.argv[2])
            state = json.loads(state_path.read_text())
            report = cleanup(db, state)
            print(json.dumps(report, indent=2))
        else:
            raise SystemExit(f"Unknown command '{command}'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
