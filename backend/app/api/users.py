from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.user import (
    UserCreate,
    UserCreatedOut,
    UserOut,
    UserStatusUpdate,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])

can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(can_view)):
    return [UserOut.from_model(user) for user in user_service.list_users(db)]


@router.post("", response_model=UserCreatedOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _=Depends(can_edit)):
    user, temporary_password = user_service.create_user(db, payload)
    return UserCreatedOut(
        **UserOut.from_model(user).model_dump(), temporary_password=temporary_password
    )


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str, payload: UserUpdate, db: Session = Depends(get_db), _=Depends(can_edit)
):
    user = user_service.update_user(db, user_service.parse_user_id(user_id), payload)
    return UserOut.from_model(user)


@router.patch("/{user_id}/status", response_model=UserOut)
def set_user_status(
    user_id: str, payload: UserStatusUpdate, db: Session = Depends(get_db), _=Depends(can_edit)
):
    user = user_service.set_user_status(db, user_service.parse_user_id(user_id), payload.status)
    return UserOut.from_model(user)
