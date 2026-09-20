from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.permit_catalog import (
    PermitCatalogItemCreate,
    PermitCatalogItemOut,
    PermitApplicationSetupUpdate,
    PermitCatalogItemUpdate,
    PermitPrerequisiteCreate,
    PermitPrerequisiteOut,
)
from app.services import permit_catalog_service, prerequisite_service

router = APIRouter(prefix="/api/permit-catalog", tags=["permit-catalog"])

# Same reasoning as service_catalog.py's can_view -- every role that can
# view/create projects needs to read the permit catalog (New Project
# wizard's Permits step), so this is gated on Projects:view rather than
# Administration:view. Only mutating the catalog is Administrator-only.
can_view = require_permission("Projects", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/permits", response_model=list[PermitCatalogItemOut])
def list_permits(db: Session = Depends(get_db), _=Depends(can_view)):
    valid_setup = permit_catalog_service.valid_setup_ids(db)
    return [PermitCatalogItemOut.from_model(p, valid_setup) for p in permit_catalog_service.list_permits(db)]


@router.post("/permits", response_model=PermitCatalogItemOut, status_code=201)
def create_permit(
    payload: PermitCatalogItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    permit = permit_catalog_service.create_permit(db, payload.name, float(payload.fixedCost), current_user.id)
    return PermitCatalogItemOut.from_model(permit)


@router.patch("/permits/{permit_id}", response_model=PermitCatalogItemOut)
def rename_permit(
    permit_id: str,
    payload: PermitCatalogItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    permit = permit_catalog_service.rename_permit(db, permit_id, payload.name, float(payload.fixedCost), current_user.id)
    return PermitCatalogItemOut.from_model(permit, permit_catalog_service.valid_setup_ids(db))


@router.put("/permits/{permit_id}/application-setup", response_model=PermitCatalogItemOut)
def set_permit_application_setup(
    permit_id: str,
    payload: PermitApplicationSetupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    permit = permit_catalog_service.set_application_setup(
        db, permit_id, payload.authorityId, payload.formId, payload.requiredDocuments, current_user.id
    )
    return PermitCatalogItemOut.from_model(permit, permit_catalog_service.valid_setup_ids(db))


@router.delete("/permits/{permit_id}", status_code=204)
def remove_permit(permit_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    permit_catalog_service.remove_permit(db, permit_id, current_user.id)


@router.get("/permits/{permit_id}/prerequisites", response_model=list[PermitPrerequisiteOut])
def list_permit_prerequisites(permit_id: str, db: Session = Depends(get_db), _=Depends(can_view)):
    return [
        PermitPrerequisiteOut.from_model(p) for p in prerequisite_service.list_permit_prerequisites(db, permit_id)
    ]


@router.post("/permits/{permit_id}/prerequisites", response_model=PermitPrerequisiteOut, status_code=201)
def add_permit_prerequisite(
    permit_id: str,
    payload: PermitPrerequisiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    prerequisite = prerequisite_service.add_permit_prerequisite(db, permit_id, payload.designActivityId)
    return PermitPrerequisiteOut.from_model(prerequisite)


@router.delete("/prerequisites/{prerequisite_id}", status_code=204)
def remove_permit_prerequisite(
    prerequisite_id: int, db: Session = Depends(get_db), current_user: User = Depends(can_edit),
):
    prerequisite_service.remove_permit_prerequisite(db, prerequisite_id)
