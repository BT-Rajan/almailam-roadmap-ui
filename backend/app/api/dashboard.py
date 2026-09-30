from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.kuwait_time import kuwait_today
from app.core.ttl_cache import TTLCache
from app.services import dashboard_service

# One request per dashboard tab, each returning ready-made figures and
# short lists -- see dashboard_service for why.
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# The figures are company-wide -- the same for everyone allowed to see a
# tab (the permission check still runs on every request, before the
# cache) -- so each tab is computed at most once per CACHE_SECONDS per
# API worker instead of once per person who opens the Dashboard. A change
# shows on the Dashboard within that time. Keyed by the Kuwait date too,
# since overdue/upcoming figures turn over at midnight. What's kept is the
# finished JSON, so a cached answer isn't re-encoded for every request
# (Financials lists every overdue agreement -- a couple of hundred KB).
CACHE_SECONDS = 30
cache = TTLCache(CACHE_SECONDS)


def _cached(tab: str, compute, db: Session) -> Response:
    body = cache.get_or_compute(
        (tab, kuwait_today()), lambda: JSONResponse(content=jsonable_encoder(compute(db))).body
    )
    return Response(content=body, media_type="application/json")


@router.get("/clients")
def clients_tab(db: Session = Depends(get_db), _=Depends(require_permission("Clients", "view"))):
    return _cached("clients", dashboard_service.clients_tab, db)


@router.get("/projects")
def projects_tab(db: Session = Depends(get_db), _=Depends(require_permission("Projects", "view"))):
    return _cached("projects", dashboard_service.projects_tab, db)


@router.get("/deadlines")
def deadlines_tab(db: Session = Depends(get_db), _=Depends(require_permission("Projects", "view"))):
    return _cached("deadlines", dashboard_service.deadlines_tab, db)


@router.get("/financials")
def financials_tab(db: Session = Depends(get_db), _=Depends(require_permission("Finance", "view"))):
    return _cached("financials", dashboard_service.financials_tab, db)
