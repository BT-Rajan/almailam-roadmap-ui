from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import RoleDefinitionOut, RoleDefinitionUpdate, RolePermissionOut
from app.services import role_service

router = APIRouter(prefix="/api/roles", tags=["roles"])

can_view = require_permission("Administration", "view")
can_edit = require_permission("Administration", "edit")


def _to_out(definition) -> RoleDefinitionOut:
    return RoleDefinitionOut(
        role=definition.role,
        description=definition.description,
        permissions=[
            RolePermissionOut(module=perm.module, view=perm.can_view, edit=perm.can_edit, delete=perm.can_delete)
            for perm in definition.permissions
        ],
    )


@router.get("", response_model=list[RoleDefinitionOut])
def list_role_definitions(db: Session = Depends(get_db), _=Depends(can_view)):
    return [_to_out(definition) for definition in role_service.list_role_definitions(db)]


@router.patch("/{role}", response_model=RoleDefinitionOut)
def update_role_permissions(
    role: str,
    payload: RoleDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_edit),
):
    definition = role_service.update_role_permissions(
        db, role, [perm.model_dump() for perm in payload.permissions], current_user.id
    )
    return _to_out(definition)
