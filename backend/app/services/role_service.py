"""Role permissions used to be a hardcoded dict (core.permissions
.ROLE_PERMISSIONS) baked into the code, which is what made the
Administration > Users > Roles & Permissions screen read-only even for
Administrators -- there was nothing in the database to write to. This
service moves that matrix into role_definitions/role_permissions
(migration 0014), seeded once from the old hardcoded values so existing
installs keep behaving exactly the same until an admin changes something.

has_permission() is called on essentially every protected request (see
api.deps.require_permission and search_service's per-category checks),
so results are cached in-process after the first DB read and the cache
is invalidated on every write -- avoids turning a single global search
into ten extra queries while still picking up admin changes immediately
within this process. Multi-worker deployments each keep their own cache;
since this is a rarely-changed admin setting (not a hot data path), a
worker briefly serving a stale permission until its next cache miss is
an acceptable tradeoff against querying the DB on every single request.
"""

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.permissions import PERMISSION_MODULES, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, ROLES
from app.models.role import RoleDefinition, RolePermission
from app.services import audit_service

ENTITY_TYPE = "ROLE_DEFINITION"

# role -> module -> {view, edit, delete}, or None until first load/write.
_CACHE: dict[str, dict[str, dict[str, bool]]] | None = None


def _invalidate_cache() -> None:
    global _CACHE
    _CACHE = None


def _ensure_seeded(db: Session) -> None:
    if db.query(RoleDefinition).first() is not None:
        return
    for role in ROLES:
        definition = RoleDefinition(role=role, description=ROLE_DESCRIPTIONS[role])
        db.add(definition)
        db.flush()
        for module in PERMISSION_MODULES:
            flags = ROLE_PERMISSIONS.get(role, {}).get(module, {})
            db.add(
                RolePermission(
                    role_id=definition.id,
                    module=module,
                    can_view=bool(flags.get("view", False)),
                    can_edit=bool(flags.get("edit", False)),
                    can_delete=bool(flags.get("delete", False)),
                )
            )
    db.commit()


def _definitions_query(db: Session):
    return db.query(RoleDefinition).options(joinedload(RoleDefinition.permissions))


def list_role_definitions(db: Session) -> list[RoleDefinition]:
    _ensure_seeded(db)
    return _definitions_query(db).order_by(RoleDefinition.id.asc()).all()


def _get_definition(db: Session, role: str) -> RoleDefinition:
    _ensure_seeded(db)
    definition = _definitions_query(db).filter(RoleDefinition.role == role).first()
    if definition is None:
        raise NotFoundError("Role")
    return definition


def _load_cache(db: Session) -> dict[str, dict[str, dict[str, bool]]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    _ensure_seeded(db)
    cache: dict[str, dict[str, dict[str, bool]]] = {}
    for definition in _definitions_query(db).all():
        cache[definition.role] = {
            perm.module: {"view": perm.can_view, "edit": perm.can_edit, "delete": perm.can_delete}
            for perm in definition.permissions
        }
    _CACHE = cache
    return cache


def has_permission(db: Session, role: str, module: str, action: str) -> bool:
    return _load_cache(db).get(role, {}).get(module, {}).get(action, False)


def update_role_permissions(
    db: Session,
    role: str,
    permissions: list[dict],
    user_id: int | None,
) -> RoleDefinition:
    definition = _get_definition(db, role)

    by_module = {perm.module: perm for perm in definition.permissions}
    incoming_modules = {entry["module"] for entry in permissions}
    unknown = incoming_modules - set(PERMISSION_MODULES)
    if unknown:
        raise ValidationAppError(f"Unknown permission module(s): {', '.join(sorted(unknown))}.")

    # Guard against an admin locking every administrator out of
    # Administration by mistake -- Administrator must always keep
    # view+edit on the Administration module itself, since that's the
    # only way anyone could ever come back and fix a bad change here.
    if role == "Administrator":
        admin_entry = next((entry for entry in permissions if entry["module"] == "Administration"), None)
        if admin_entry is not None and not (admin_entry["view"] and admin_entry["edit"]):
            raise ValidationAppError(
                "Administrator must keep view and edit access to the Administration module."
            )

    changes: dict[str, tuple] = {}
    for entry in permissions:
        module = entry["module"]
        row = by_module.get(module)
        if row is None:
            row = RolePermission(role_id=definition.id, module=module)
            db.add(row)
            by_module[module] = row

        for field, key in (("view", "can_view"), ("edit", "can_edit"), ("delete", "can_delete")):
            old = getattr(row, key)
            new = bool(entry[field])
            if old != new:
                changes[f"{module} {field}"] = (old, new)
            setattr(row, key, new)

    db.commit()
    db.refresh(definition)

    if changes:
        audit_service.log_field_changes(
            db, ENTITY_TYPE, definition.id, changes, user_id, label_prefix=f"Updated {role} permission -"
        )

    _invalidate_cache()
    return definition
