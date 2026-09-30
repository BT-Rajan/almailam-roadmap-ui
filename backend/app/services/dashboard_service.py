"""Dashboard figures, computed in the database.

The dashboard used to download every client, project, task, document,
contract, payment agreement and instalment in the company and count them
in the browser -- the first page everyone lands on, getting slower as the
data grew. Each tab now gets its numbers and short, bounded lists from
one request here instead: counts are SQL aggregates, lists are capped
(newest / soonest first) with the total alongside, and every name a row
shows is resolved server-side.
"""

from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.file_storage import format_file_size
from app.core.kuwait_time import kuwait_today
from app.models.client import Client
from app.models.contract import Contract
from app.models.document import ProjectDocument
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import payment_service

# How many rows each list sends. The widgets page through these a few at
# a time; anything beyond is one click away on the full page (Clients,
# Projects, My Tasks, Documents, Payments).
RECENT_CLIENTS_LIMIT = 30
RECENT_PROJECTS_LIMIT = 24
PENDING_TASKS_LIMIT = 25
RECENT_DOCUMENTS_LIMIT = 25
UPCOMING_DEADLINES_LIMIT = 100

# Onboarding still in progress -- see DashboardClientsTab.vue.
ONBOARDING_IN_PROGRESS = ("Information Required", "Documents Required", "Pending Verification")
# A contract only counts down to expiry once it's in force.
RENEWAL_ELIGIBLE_CONTRACT_STATUSES = ("Signed", "Active")


def _user_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    return {u.id: u.full_name for u in db.query(User.id, User.full_name).filter(User.id.in_(user_ids)).all()}


def _project_names(db: Session, project_ids: set[int]) -> dict[int, tuple[str, str]]:
    """project id -> (project_no, project_name), one query."""
    if not project_ids:
        return {}
    rows = db.query(Project.id, Project.project_no, Project.project_name).filter(Project.id.in_(project_ids)).all()
    return {row[0]: (row[1], row[2]) for row in rows}


def clients_tab(db: Session) -> dict:
    live = db.query(Client).filter(Client.deleted_at.is_(None))
    counts = dict(
        live.with_entities(Client.status, func.count(Client.id)).group_by(Client.status).all()
    )
    onboarding = live.filter(Client.onboarding_state.in_(ONBOARDING_IN_PROGRESS)).count()
    recent = live.order_by(Client.created_at.desc(), Client.id.desc()).limit(RECENT_CLIENTS_LIMIT).all()
    return {
        "total": sum(counts.values()),
        "active": counts.get("Active", 0),
        "inactive": counts.get("Inactive", 0),
        "onboarding": onboarding,
        "recentClients": [
            {
                "id": f"CLT-{c.id:03d}",  # same public id ClientOut uses
                "name": c.company_name,
                "type": c.client_type,
                "status": c.status,
                "city": c.city,
                "createdDate": c.created_at.date().isoformat(),
            }
            for c in recent
        ],
    }


def projects_tab(db: Session) -> dict:
    live_projects = db.query(Project).filter(Project.deleted_at.is_(None))
    counts = dict(
        live_projects.with_entities(Project.status, func.count(Project.id)).group_by(Project.status).all()
    )

    recent_rows = (
        db.query(Project, Client.company_name)
        .outerjoin(Client, Client.id == Project.client_id)
        .filter(Project.deleted_at.is_(None))
        .order_by(Project.id.desc())
        .limit(RECENT_PROJECTS_LIMIT)
        .all()
    )

    open_tasks = db.query(Task).filter(Task.deleted_at.is_(None), Task.status != "Completed")
    pending_total = open_tasks.count()
    pending = open_tasks.order_by(Task.due_date.asc(), Task.id.asc()).limit(PENDING_TASKS_LIMIT).all()

    documents = db.query(ProjectDocument).filter(ProjectDocument.deleted_at.is_(None))
    documents_total = documents.count()
    recent_documents = (
        documents.order_by(ProjectDocument.upload_date.desc(), ProjectDocument.id.desc())
        .limit(RECENT_DOCUMENTS_LIMIT)
        .all()
    )

    projects = _project_names(db, {t.project_id for t in pending} | {d.project_id for d in recent_documents})
    users = _user_names(db, {t.assigned_to for t in pending if t.assigned_to} | {d.uploaded_by for d in recent_documents})

    return {
        "total": sum(counts.values()),
        "active": counts.get("Active", 0),
        "onHold": counts.get("On Hold", 0),
        "recentProjects": [
            {
                "id": p.project_no,
                "name": p.project_name,
                "client": client_name or "",
                "status": p.status,
                "progress": p.progress,
                "dueDate": p.target_date.isoformat(),
                "siteAddress": p.site_address,
            }
            for p, client_name in recent_rows
        ],
        "pendingTasksTotal": pending_total,
        "pendingTasks": [
            {
                "id": t.task_no,
                "title": t.title,
                "project": projects.get(t.project_id, ("", ""))[1],
                "priority": t.priority,
                "assignee": users.get(t.assigned_to, "Unassigned"),
                "dueDate": t.due_date.isoformat(),
                "status": t.status,
            }
            for t in pending
        ],
        "documentsTotal": documents_total,
        "recentDocuments": [
            {
                "id": d.document_no,
                "name": d.title,
                "project": projects.get(d.project_id, ("", ""))[1],
                "type": d.type,
                "uploadedAt": d.upload_date.isoformat(),
                "uploadedBy": users.get(d.uploaded_by, "Unknown"),
                "size": format_file_size(d.file_size_bytes) if d.file_size_bytes is not None else None,
            }
            for d in recent_documents
        ],
    }


def deadlines_tab(db: Session) -> dict:
    today = kuwait_today()
    open_tasks = db.query(Task).filter(Task.deleted_at.is_(None), Task.status != "Completed")
    overdue_tasks = open_tasks.filter(Task.due_date < today).count()
    upcoming = (
        open_tasks.filter(Task.due_date >= today, Task.due_date <= today + timedelta(days=14))
        .order_by(Task.due_date.asc(), Task.id.asc())
        .limit(UPCOMING_DEADLINES_LIMIT)
        .all()
    )

    # Contracts in force that expire within a week, or have already
    # expired while their (non-deleted) project is still not Completed.
    contracts = (
        db.query(Contract, Project.project_no, Project.project_name, Project.status)
        .join(Project, Project.id == Contract.project_id)
        .filter(
            Contract.deleted_at.is_(None),
            Project.deleted_at.is_(None),
            Contract.status.in_(RENEWAL_ELIGIBLE_CONTRACT_STATUSES),
            Contract.expiry_date <= today + timedelta(days=7),
        )
        .order_by(Contract.expiry_date.asc())
        .all()
    )
    expiring_soon, not_renewed = [], []
    for contract, project_no, project_name, project_status in contracts:
        row = {
            "contractNo": contract.contract_no,
            "projectId": project_no,
            "project": project_name,
            "expiryDate": contract.expiry_date.isoformat(),
        }
        if contract.expiry_date >= today:
            expiring_soon.append(row)
        elif project_status != "Completed":
            not_renewed.append(row)

    projects = _project_names(db, {t.project_id for t in upcoming})
    return {
        "overdueTasks": overdue_tasks,
        "upcomingDeadlines": [
            {
                "id": t.task_no,
                "title": t.title,
                "project": projects.get(t.project_id, ("", ""))[1],
                "dueDate": t.due_date.isoformat(),
                "priority": t.priority,
            }
            for t in upcoming
        ],
        "contractsExpiringSoon": expiring_soon,
        "contractsNotRenewed": not_renewed,
    }


def financials_tab(db: Session) -> dict:
    """Portfolio pending/overdue totals and the agreements with anything
    overdue -- computed by payment_service.agreements_overview, the same
    source the Payments page uses, so the two always agree."""
    overview = payment_service.agreements_overview(db)
    overdue_agreements = [
        {
            "id": row["id"],
            "projectId": row["projectId"],
            "project": row["projectName"],
            "client": row["clientName"],
            "overdueAmount": row["totalOverdue"],
            "currency": row["currency"],
        }
        for row in overview["rows"]
        if row["totalOverdue"] > 0
    ]
    overdue_agreements.sort(key=lambda row: row["overdueAmount"], reverse=True)
    return {
        "totalPending": overview["totals"]["totalPending"],
        "totalOverdue": overview["totals"]["totalOverdue"],
        "overdueAgreements": overdue_agreements,
    }
