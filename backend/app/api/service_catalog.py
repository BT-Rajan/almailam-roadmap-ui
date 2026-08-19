from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.service_catalog import (
    ServiceCatalogActivityCreate,
    ServiceCatalogActivityOut,
    ServiceCatalogActivityUpdate,
    ServiceCatalogItemCreate,
    ServiceCatalogItemOut,
    ServiceCatalogItemUpdate,
)
from app.services import service_catalog_service

router = APIRouter(prefix="/api/service-catalog", tags=["service-catalog"])

# Service catalog configuration is Administration-level settings, same
# module the workflow templates and government forms admin pages are
# gated behind.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/services", response_model=list[ServiceCatalogItemOut])
def list_services(db: Session = Depends(get_db), _=Depends(can_view)):
    return [ServiceCatalogItemOut.from_model(s) for s in service_catalog_service.list_services(db)]


@router.post("/services", response_model=ServiceCatalogItemOut, status_code=201)
def create_service(
    payload: ServiceCatalogItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    service = service_catalog_service.create_service(db, payload.name, current_user.id)
    return ServiceCatalogItemOut.from_model(service)


@router.patch("/services/{service_id}", response_model=ServiceCatalogItemOut)
def rename_service(
    service_id: str,
    payload: ServiceCatalogItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    service = service_catalog_service.rename_service(db, service_id, payload.name, current_user.id)
    return ServiceCatalogItemOut.from_model(service)


@router.delete("/services/{service_id}", status_code=204)
def remove_service(service_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    service_catalog_service.remove_service(db, service_id, current_user.id)


@router.post("/services/{service_id}/activities", response_model=ServiceCatalogActivityOut, status_code=201)
def add_activity(
    service_id: str,
    payload: ServiceCatalogActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    activity = service_catalog_service.add_activity(db, service_id, payload.name, payload.fixedCost, current_user.id)
    return ServiceCatalogActivityOut.from_model(activity)


@router.patch("/activities/{activity_id}", response_model=ServiceCatalogActivityOut)
def update_activity(
    activity_id: str,
    payload: ServiceCatalogActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    activity = service_catalog_service.update_activity(
        db, activity_id, payload.name, payload.fixedCost, current_user.id,
    )
    return ServiceCatalogActivityOut.from_model(activity)


@router.delete("/activities/{activity_id}", status_code=204)
def remove_activity(activity_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    service_catalog_service.remove_activity(db, activity_id, current_user.id)
