from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.permissions import has_permission
from app.models.client import Client
from app.models.government import GovernmentForm
from app.models.project import Project
from app.models.document import ProjectDocument
from app.models.task import Task
from app.models.user import User
from app.schemas.search import SearchResult

RESULTS_PER_CATEGORY = 8


def _term(raw: str) -> str:
    # Escape SQL LIKE wildcards in the user-supplied term so a search for
    # e.g. "50%" or "a_b" can't be used to widen matches beyond what the
    # user typed. Values are still bound as query parameters by SQLAlchemy,
    # so this is a correctness fix for wildcard characters, not an
    # injection concern.
    escaped = raw.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _search_clients(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    digits = "".join(ch for ch in term if ch.isdigit())
    conditions = [
        Client.company_name.ilike(like, escape="\\"),
        Client.contact_person.ilike(like, escape="\\"),
        Client.email.ilike(like, escape="\\"),
    ]
    if digits:
        conditions.append(Client.mobile.contains(digits))
    clients = (
        db.query(Client)
        .filter(Client.deleted_at.is_(None), or_(*conditions))
        .order_by(Client.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    return [
        SearchResult(
            id=f"CLT-{client.id:03d}",
            category="Client",
            title=client.company_name,
            subtitle=f"{client.client_type} · {client.status}",
            routeName="client-workspace",
            params={"clientId": f"CLT-{client.id:03d}"},
        )
        for client in clients
    ]


def _search_projects(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    projects = (
        db.query(Project)
        .filter(
            Project.deleted_at.is_(None),
            or_(
                Project.project_no.ilike(like, escape="\\"),
                Project.project_name.ilike(like, escape="\\"),
                Project.service.ilike(like, escape="\\"),
            ),
        )
        .order_by(Project.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    return [
        SearchResult(
            id=project.project_no,
            category="Project",
            title=project.project_name,
            subtitle=f"{project.service} · {project.status}",
            routeName="project-workspace",
            params={"projectId": project.project_no},
        )
        for project in projects
    ]


def _search_documents(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    documents = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.deleted_at.is_(None),
            or_(
                ProjectDocument.document_no.ilike(like, escape="\\"),
                ProjectDocument.title.ilike(like, escape="\\"),
                ProjectDocument.type.ilike(like, escape="\\"),
            ),
        )
        .order_by(ProjectDocument.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    return [
        SearchResult(
            id=document.document_no,
            category="Document",
            title=document.title,
            subtitle=f"{document.type} · {document.status}",
            routeName="document-viewer",
            params={"documentId": document.document_no},
        )
        for document in documents
    ]


def _search_forms(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    forms = (
        db.query(GovernmentForm)
        .filter(
            GovernmentForm.deleted_at.is_(None),
            or_(
                GovernmentForm.form_code.ilike(like, escape="\\"),
                GovernmentForm.title.ilike(like, escape="\\"),
                GovernmentForm.category.ilike(like, escape="\\"),
            ),
        )
        .order_by(GovernmentForm.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    return [
        SearchResult(
            id=f"FORM-{form.id:03d}",
            category="Form",
            title=form.title,
            subtitle=f"{form.form_code} · {form.category}",
            routeName="government-forms",
        )
        for form in forms
    ]


def _search_tasks(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    tasks = (
        db.query(Task)
        .filter(
            Task.deleted_at.is_(None),
            or_(
                Task.task_no.ilike(like, escape="\\"),
                Task.title.ilike(like, escape="\\"),
            ),
        )
        .order_by(Task.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    if not tasks:
        return []

    assignee_ids = {task.assigned_to for task in tasks}
    names = {
        user.id: user.full_name
        for user in db.query(User).filter(User.id.in_(assignee_ids)).all()
    }
    return [
        SearchResult(
            id=task.task_no,
            category="Task",
            title=task.title,
            subtitle=f"{names.get(task.assigned_to, 'Unassigned')} · {task.status}",
            routeName="tasks",
        )
        for task in tasks
    ]


def _search_users(db: Session, term: str) -> list[SearchResult]:
    like = _term(term)
    users = (
        db.query(User)
        .filter(
            User.deleted_at.is_(None),
            or_(
                User.full_name.ilike(like, escape="\\"),
                User.email.ilike(like, escape="\\"),
                User.username.ilike(like, escape="\\"),
                User.designation.ilike(like, escape="\\"),
            ),
        )
        .order_by(User.id.asc())
        .limit(RESULTS_PER_CATEGORY)
        .all()
    )
    return [
        SearchResult(
            id=f"USR-{user.id:03d}",
            category="User",
            title=user.full_name,
            subtitle=f"{user.designation or user.role} · {user.role}",
            routeName="admin-users",
        )
        for user in users
    ]


# Each category is gated behind the same permission the module's own list
# endpoint requires, so the global search box can never surface data the
# requesting user isn't otherwise allowed to see.
_CATEGORY_SEARCHERS = (
    ("Clients", "view", _search_clients),
    ("Projects", "view", _search_projects),
    ("Documents", "view", _search_documents),
    ("Government", "view", _search_forms),
    ("Projects", "view", _search_tasks),
    ("Administration", "view", _search_users),
)


def global_search(db: Session, term: str, user_role: str) -> list[SearchResult]:
    term = term.strip()
    if not term:
        return []

    results: list[SearchResult] = []
    for module, action, searcher in _CATEGORY_SEARCHERS:
        if has_permission(user_role, module, action):
            results.extend(searcher(db, term))
    return results


def search_clients(db: Session, term: str, user_role: str) -> list[SearchResult]:
    if not term.strip() or not has_permission(user_role, "Clients", "view"):
        return []
    return _search_clients(db, term)


def search_projects(db: Session, term: str, user_role: str) -> list[SearchResult]:
    if not term.strip() or not has_permission(user_role, "Projects", "view"):
        return []
    return _search_projects(db, term)


def search_documents(db: Session, term: str, user_role: str) -> list[SearchResult]:
    if not term.strip() or not has_permission(user_role, "Documents", "view"):
        return []
    return _search_documents(db, term)


def search_users(db: Session, term: str, user_role: str) -> list[SearchResult]:
    if not term.strip() or not has_permission(user_role, "Administration", "view"):
        return []
    return _search_users(db, term)
