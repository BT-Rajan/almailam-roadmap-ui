from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.search import SearchResult
from app.services import search_service

router = APIRouter(prefix="/api/search", tags=["search"])

# A bare Query(..., max_length=...) guards against pathologically long
# terms being sent through to ILIKE scans on every table.
QueryTerm = Query(default="", max_length=200)


@router.get("", response_model=list[SearchResult])
def search(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.global_search(db, q, current_user.role)


@router.get("/clients", response_model=list[SearchResult])
def search_clients(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_clients(db, q, current_user.role)


@router.get("/projects", response_model=list[SearchResult])
def search_projects(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_projects(db, q, current_user.role)


@router.get("/documents", response_model=list[SearchResult])
def search_documents(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_documents(db, q, current_user.role)


@router.get("/users", response_model=list[SearchResult])
def search_users(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_users(db, q, current_user.role)


@router.get("/contracts", response_model=list[SearchResult])
def search_contracts(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_contracts(db, q, current_user.role)


@router.get("/quotations", response_model=list[SearchResult])
def search_quotations(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_quotations(db, q, current_user.role)


@router.get("/submissions", response_model=list[SearchResult])
def search_submissions(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_submissions(db, q, current_user.role)


@router.get("/payments", response_model=list[SearchResult])
def search_payments(
    q: str = QueryTerm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_service.search_payments(db, q, current_user.role)
