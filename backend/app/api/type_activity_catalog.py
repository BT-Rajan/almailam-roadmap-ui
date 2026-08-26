from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.type_activity_catalog import (
    TypeActivityCategoryCreate,
    TypeActivityCategoryOut,
    TypeActivityCategoryUpdate,
    TypeActivityItemCreate,
    TypeActivityItemOut,
    TypeActivityItemUpdate,
)
from app.services import type_activity_catalog_service

router = APIRouter(prefix="/api/type-activity-catalog", tags=["type-activity-catalog"])

# Same gating as service-catalog and permit-catalog: this is
# Administration-level configuration. Reading the list to populate the
# New Project wizard's final-step picker only needs "view", same as any
# other project-creation dropdown -- it isn't gated behind Projects
# permissions specifically, since every role that can create a project
# can already see the service catalog the same way.
can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("/categories", response_model=list[TypeActivityCategoryOut])
def list_categories(db: Session = Depends(get_db), _=Depends(can_view)):
    return [TypeActivityCategoryOut.from_model(c) for c in type_activity_catalog_service.list_categories(db)]


@router.post("/categories", response_model=TypeActivityCategoryOut, status_code=201)
def create_category(
    payload: TypeActivityCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    category = type_activity_catalog_service.create_category(db, payload.name, current_user.id)
    return TypeActivityCategoryOut.from_model(category)


@router.patch("/categories/{category_id}", response_model=TypeActivityCategoryOut)
def rename_category(
    category_id: str,
    payload: TypeActivityCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    category = type_activity_catalog_service.rename_category(db, category_id, payload.name, current_user.id)
    return TypeActivityCategoryOut.from_model(category)


@router.delete("/categories/{category_id}", status_code=204)
def remove_category(category_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    type_activity_catalog_service.remove_category(db, category_id, current_user.id)


@router.post("/categories/{category_id}/activities", response_model=TypeActivityItemOut, status_code=201)
def add_activity(
    category_id: str,
    payload: TypeActivityItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    item = type_activity_catalog_service.add_item(db, category_id, payload.name, payload.cost, current_user.id)
    return TypeActivityItemOut.from_model(item)


@router.patch("/activities/{activity_id}", response_model=TypeActivityItemOut)
def update_activity(
    activity_id: str,
    payload: TypeActivityItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    item = type_activity_catalog_service.update_item(db, activity_id, payload.name, payload.cost, current_user.id)
    return TypeActivityItemOut.from_model(item)


@router.delete("/activities/{activity_id}", status_code=204)
def remove_activity(activity_id: str, db: Session = Depends(get_db), current_user: User = Depends(can_edit)):
    type_activity_catalog_service.remove_item(db, activity_id, current_user.id)
