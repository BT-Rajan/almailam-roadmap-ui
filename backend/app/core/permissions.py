# ROLES/PERMISSION_MODULES stay fixed constants (used for the users.role
# DB enum and request validation). ROLE_DESCRIPTIONS/ROLE_PERMISSIONS
# below are seed defaults only, used once to populate role_definitions/
# role_permissions on first run (see role_service._ensure_seeded) -- the
# database is the actual source of truth after that, editable from
# Administration > Users > Roles & Permissions. Runtime permission checks
# go through role_service.has_permission(), not these dicts.
ROLES = ("Administrator", "Project Manager", "Engineer", "Document Controller", "Viewer")

PERMISSION_MODULES = ("Projects", "Clients", "Documents", "Government", "Finance", "Reports", "Administration")

ROLE_DESCRIPTIONS: dict[str, str] = {
    "Administrator": "Full access to every module, including administration and system configuration.",
    "Project Manager": "Manages project delivery, documents, government submissions, financial agreements, and reporting.",
    "Engineer": "Works on assigned projects and documents, with read access to government tracking and financial status.",
    "Document Controller": "Maintains the document repository and revision history across projects, and onboards clients.",
    "Viewer": "Read-only access for stakeholders who need visibility without edit rights.",
}

# role -> module -> {view, edit, delete}
ROLE_PERMISSIONS: dict[str, dict[str, dict[str, bool]]] = {
    "Administrator": {
        "Projects": {"view": True, "edit": True, "delete": True},
        "Clients": {"view": True, "edit": True, "delete": True},
        "Documents": {"view": True, "edit": True, "delete": True},
        "Government": {"view": True, "edit": True, "delete": True},
        "Finance": {"view": True, "edit": True, "delete": True},
        "Reports": {"view": True, "edit": True, "delete": True},
        "Administration": {"view": True, "edit": True, "delete": True},
    },
    "Project Manager": {
        "Projects": {"view": True, "edit": True, "delete": False},
        "Clients": {"view": True, "edit": True, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": False},
        "Government": {"view": True, "edit": True, "delete": False},
        "Finance": {"view": True, "edit": True, "delete": False},
        "Reports": {"view": True, "edit": True, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Engineer": {
        "Projects": {"view": True, "edit": True, "delete": False},
        "Clients": {"view": True, "edit": True, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": False},
        "Government": {"view": True, "edit": False, "delete": False},
        "Finance": {"view": True, "edit": False, "delete": False},
        "Reports": {"view": True, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Document Controller": {
        "Projects": {"view": True, "edit": False, "delete": False},
        "Clients": {"view": True, "edit": True, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": True},
        "Government": {"view": True, "edit": False, "delete": False},
        "Finance": {"view": False, "edit": False, "delete": False},
        "Reports": {"view": False, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Viewer": {
        "Projects": {"view": True, "edit": False, "delete": False},
        "Clients": {"view": True, "edit": False, "delete": False},
        "Documents": {"view": True, "edit": False, "delete": False},
        "Government": {"view": True, "edit": False, "delete": False},
        "Finance": {"view": True, "edit": False, "delete": False},
        "Reports": {"view": True, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
}


