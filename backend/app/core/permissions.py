ROLES = ("Administrator", "Project Manager", "Engineer", "Document Controller", "Viewer")

PERMISSION_MODULES = ("Projects", "Documents", "Government", "Reports", "Administration")

ROLE_DESCRIPTIONS: dict[str, str] = {
    "Administrator": "Full access to every module, including administration and system configuration.",
    "Project Manager": "Manages project delivery, documents, government submissions, and reporting.",
    "Engineer": "Works on assigned projects and documents, with read access to government tracking.",
    "Document Controller": "Maintains the document repository and revision history across projects.",
    "Viewer": "Read-only access for stakeholders who need visibility without edit rights.",
}

# role -> module -> {view, edit, delete}
ROLE_PERMISSIONS: dict[str, dict[str, dict[str, bool]]] = {
    "Administrator": {
        "Projects": {"view": True, "edit": True, "delete": True},
        "Documents": {"view": True, "edit": True, "delete": True},
        "Government": {"view": True, "edit": True, "delete": True},
        "Reports": {"view": True, "edit": True, "delete": True},
        "Administration": {"view": True, "edit": True, "delete": True},
    },
    "Project Manager": {
        "Projects": {"view": True, "edit": True, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": False},
        "Government": {"view": True, "edit": True, "delete": False},
        "Reports": {"view": True, "edit": True, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Engineer": {
        "Projects": {"view": True, "edit": True, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": False},
        "Government": {"view": True, "edit": False, "delete": False},
        "Reports": {"view": True, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Document Controller": {
        "Projects": {"view": True, "edit": False, "delete": False},
        "Documents": {"view": True, "edit": True, "delete": True},
        "Government": {"view": True, "edit": False, "delete": False},
        "Reports": {"view": False, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
    "Viewer": {
        "Projects": {"view": True, "edit": False, "delete": False},
        "Documents": {"view": True, "edit": False, "delete": False},
        "Government": {"view": True, "edit": False, "delete": False},
        "Reports": {"view": True, "edit": False, "delete": False},
        "Administration": {"view": False, "edit": False, "delete": False},
    },
}


def has_permission(role: str, module: str, action: str) -> bool:
    return ROLE_PERMISSIONS.get(role, {}).get(module, {}).get(action, False)
