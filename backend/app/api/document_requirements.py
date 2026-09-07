from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.document_requirement import (
    DocumentRequirementCreate,
    DocumentRequirementLinkCreate,
    DocumentRequirementLinkOut,
    DocumentRequirementOut,
    DocumentRequirementUpdate,
)
from app.services import document_requirement_service

router = APIRouter(prefix="/api/document-requirements", tags=["document-requirements"])

# Same reasoning as service_catalog.py/permit_catalog.py's can_view --
# every role that can view projects needs to read this (a project's own
# tabs show it as a reference checklist), only mutating it is
# Administrator-only.
can_view = require_permission("Projects", "view")
can_edit = require_permission("Administration", "edit")


@router.get("", response_model=list[DocumentRequirementOut])
def list_requirements(db: Session = Depends(get_db), _=Depends(can_view)):
    return [DocumentRequirementOut.from_model(r) for r in document_requirement_service.list_requirements(db)]


@router.post("", response_model=DocumentRequirementOut, status_code=201)
def create_requirement(
    payload: DocumentRequirementCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    requirement = document_requirement_service.create_requirement(db, payload.name, payload.description, current_user.id)
    return DocumentRequirementOut.from_model(requirement)


@router.patch("/{requirement_id}", response_model=DocumentRequirementOut)
def update_requirement(
    requirement_id: str,
    payload: DocumentRequirementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    requirement = document_requirement_service.update_requirement(
        db, requirement_id, payload.name, payload.description, current_user.id,
    )
    return DocumentRequirementOut.from_model(requirement)


@router.delete("/{requirement_id}", status_code=204)
def remove_requirement(requirement_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    document_requirement_service.remove_requirement(db, requirement_id, current_user.id)


def _link_out(db: Session, link) -> DocumentRequirementLinkOut:
    requirement = document_requirement_service.get_requirement(db, str(link.document_requirement_id))
    return DocumentRequirementLinkOut.from_model(link, requirement)


@router.get("/links", response_model=list[DocumentRequirementLinkOut])
def list_links_for_target(
    targetType: str = Query(...), targetCatalogId: str = Query(...),
    db: Session = Depends(get_db), _=Depends(can_view),
):
    return [_link_out(db, link) for link in document_requirement_service.list_links_for_target(db, targetType, targetCatalogId)]


@router.get("/{requirement_id}/links", response_model=list[DocumentRequirementLinkOut])
def list_links_for_requirement(requirement_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return [_link_out(db, link) for link in document_requirement_service.list_links_for_requirement(db, requirement_id)]


@router.post("/links", response_model=DocumentRequirementLinkOut, status_code=201)
def add_link(
    payload: DocumentRequirementLinkCreate, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    link = document_requirement_service.add_link(
        db, payload.requirementId, payload.targetType, payload.targetCatalogId,
    )
    return _link_out(db, link)


@router.delete("/links/{link_id}", status_code=204)
def remove_link(link_id: int, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    document_requirement_service.remove_link(db, link_id)
