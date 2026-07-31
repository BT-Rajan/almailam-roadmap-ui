from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core.permissions import ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, ROLES
from app.schemas.user import RoleDefinitionOut, RolePermissionOut

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RoleDefinitionOut])
def list_role_definitions(_=Depends(require_permission("Administration", "view"))):
    return [
        RoleDefinitionOut(
            role=role,
            description=ROLE_DESCRIPTIONS[role],
            permissions=[
                RolePermissionOut(module=module, **ROLE_PERMISSIONS[role][module])
                for module in ROLE_PERMISSIONS[role]
            ],
        )
        for role in ROLES
    ]
