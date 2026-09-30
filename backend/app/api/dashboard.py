from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.services import dashboard_service

# One request per dashboard tab, each returning ready-made figures and
# short lists -- see dashboard_service for why.
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/clients")
def clients_tab(db: Session = Depends(get_db), _=Depends(require_permission("Clients", "view"))):
    return dashboard_service.clients_tab(db)


@router.get("/projects")
def projects_tab(db: Session = Depends(get_db), _=Depends(require_permission("Projects", "view"))):
    return dashboard_service.projects_tab(db)


@router.get("/deadlines")
def deadlines_tab(db: Session = Depends(get_db), _=Depends(require_permission("Projects", "view"))):
    return dashboard_service.deadlines_tab(db)


@router.get("/financials")
def financials_tab(db: Session = Depends(get_db), _=Depends(require_permission("Finance", "view"))):
    return dashboard_service.financials_tab(db)
