from calendar import month_abbr
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.contract import Contract
from app.models.document import ProjectDocument
from app.models.government import GovernmentSubmission
from app.models.payment import FinancialAgreement, Payment, PaymentObligation
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.task import Task
from app.services.payment_service import get_financial_summary


def _status_color(status: str) -> str:
    negative = ("Reject", "Cancel", "Terminat", "Overdue", "Suspend")
    positive = ("Approv", "Complet", "Sign", "Paid", "Active", "Ready")
    if any(word in status for word in negative):
        return "danger"
    if any(word in status for word in positive):
        return "success"
    return "info"


def _count_by(db: Session, model, column) -> list[dict]:
    query = db.query(column, func.count(model.id))
    if hasattr(model, "deleted_at"):
        query = query.filter(model.deleted_at.is_(None))
    rows = query.group_by(column).all()
    return [{"label": label, "value": count, "color": _status_color(label)} for label, count in rows]


def projects_by_status(db: Session) -> list[dict]:
    return _count_by(db, Project, Project.status)


def projects_by_priority(db: Session) -> list[dict]:
    return _count_by(db, Project, Project.priority)


def tasks_by_status(db: Session) -> list[dict]:
    return _count_by(db, Task, Task.status)


def tasks_by_priority(db: Session) -> list[dict]:
    return _count_by(db, Task, Task.priority)


def submissions_by_status(db: Session) -> list[dict]:
    return _count_by(db, GovernmentSubmission, GovernmentSubmission.status)


def quotations_by_status(db: Session) -> list[dict]:
    return _count_by(db, Quotation, Quotation.status)


def contracts_by_status(db: Session) -> list[dict]:
    return _count_by(db, Contract, Contract.status)


def documents_by_status(db: Session) -> list[dict]:
    return _count_by(db, ProjectDocument, ProjectDocument.status)


def payments_received_by_month(db: Session, months: int = 6) -> list[dict]:
    today = date.today()
    year, month = today.year, today.month
    buckets: list[tuple[int, int]] = []
    for _ in range(months):
        buckets.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    buckets.reverse()

    rows = (
        db.query(
            func.year(Payment.payment_date),
            func.month(Payment.payment_date),
            func.sum(Payment.amount_received),
        )
        .group_by(func.year(Payment.payment_date), func.month(Payment.payment_date))
        .all()
    )
    totals = {(int(y), int(m)): float(total) for y, m, total in rows}

    return [{"x": f"{month_abbr[m]} {y}", "value": totals.get((y, m), 0.0)} for y, m in buckets]


def summary_metrics(db: Session) -> list[dict]:
    total_projects = db.query(func.count(Project.id)).filter(Project.deleted_at.is_(None)).scalar() or 0
    active_projects = (
        db.query(func.count(Project.id))
        .filter(Project.deleted_at.is_(None), Project.status == "Active")
        .scalar()
        or 0
    )
    on_hold_projects = (
        db.query(func.count(Project.id))
        .filter(Project.deleted_at.is_(None), Project.status == "On Hold")
        .scalar()
        or 0
    )
    total_clients = db.query(func.count(Client.id)).filter(Client.deleted_at.is_(None)).scalar() or 0
    open_tasks = (
        db.query(func.count(Task.id)).filter(Task.deleted_at.is_(None), Task.status != "Completed").scalar() or 0
    )
    overdue_tasks = (
        db.query(func.count(Task.id))
        .filter(Task.deleted_at.is_(None), Task.status != "Completed", Task.due_date < date.today())
        .scalar()
        or 0
    )
    total_received = db.query(func.sum(PaymentObligation.amount_received)).scalar() or 0
    total_pending = (
        db.query(func.sum(PaymentObligation.amount_due - PaymentObligation.amount_received))
        .filter(PaymentObligation.manual_status.is_(None))
        .scalar()
        or 0
    )

    return [
        {"label": "Total Projects", "value": total_projects, "color": "primary"},
        {"label": "Active Projects", "value": active_projects, "color": "success"},
        {"label": "On Hold Projects", "value": on_hold_projects, "color": "info"},
        {"label": "Total Clients", "value": total_clients, "color": "primary"},
        {"label": "Open Tasks", "value": open_tasks, "color": "warning"},
        {"label": "Overdue Tasks", "value": overdue_tasks, "color": "danger"},
        {"label": "Total Received", "value": float(total_received), "unit": "KWD", "color": "success"},
        {"label": "Total Pending", "value": float(total_pending), "unit": "KWD", "color": "warning"},
    ]


def _ledger_project_client_filter(query, project_no: str | None, client_id: int | None):
    if project_no:
        query = query.filter(Project.project_no == project_no)
    if client_id is not None:
        query = query.filter(Project.client_id == client_id)
    return query


def payment_ledger(
    db: Session, project_no: str | None = None, client_id: int | None = None,
    start_date: date | None = None, end_date: date | None = None,
) -> list[dict]:
    """The actual, recorded ledger -- one row per Payment ever received,
    joined to the project/agreement it was recorded against so it can be
    filtered project-wise or client-wise (and by date) without the
    caller having to resolve those joins itself. Payment is otherwise
    immutable once recorded (see its own model comment), so this is a
    straightforward append-only history, not a computed balance."""
    query = (
        db.query(Payment, Project, FinancialAgreement)
        .join(Project, Payment.project_id == Project.id)
        .join(FinancialAgreement, Payment.agreement_id == FinancialAgreement.id)
    )
    query = _ledger_project_client_filter(query, project_no, client_id)
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    rows = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()

    client_ids = {project.client_id for _, project, _ in rows}
    client_names = (
        {c.id: c.company_name for c in db.query(Client).filter(Client.id.in_(client_ids)).all()} if client_ids else {}
    )

    return [
        {
            "paymentNo": f"PMT-{payment.id:03d}",
            "date": payment.payment_date.isoformat(),
            "projectNo": project.project_no,
            "projectName": project.project_name,
            "clientName": client_names.get(project.client_id, ""),
            "service": agreement.stream,
            "amount": float(payment.amount_received),
            "currency": agreement.currency,
            "mode": payment.payment_mode,
            "reference": payment.reference_number,
            "payer": payment.payer,
        }
        for payment, project, agreement in rows
    ]


def _outstanding_obligations_query(db: Session, project_no: str | None, client_id: int | None):
    """Every obligation still owed -- due minus received is positive and
    it hasn't been manually written off (Cancelled/Waived, see
    OBLIGATION_OVERRIDE_ALLOWED_TRANSITIONS) -- the same "what's left to
    collect" definition summary_metrics' totalPending already uses,
    scoped down to one project/client when asked."""
    query = (
        db.query(PaymentObligation, FinancialAgreement, Project)
        .join(FinancialAgreement, PaymentObligation.agreement_id == FinancialAgreement.id)
        .join(Project, FinancialAgreement.project_id == Project.id)
        .filter(PaymentObligation.manual_status.is_(None))
        .filter((PaymentObligation.amount_due - PaymentObligation.amount_received) > 0)
    )
    return _ledger_project_client_filter(query, project_no, client_id)


def payment_projections(db: Session, project_no: str | None = None, client_id: int | None = None) -> dict:
    """Expected-but-not-yet-received income, grouped three ways -- by the
    month it falls due, by project, and by service (agreement stream) --
    so "what's still coming in" can be read whichever way is useful,
    without three separate round trips."""
    rows = _outstanding_obligations_query(db, project_no, client_id).all()

    by_month: dict[str, float] = {}
    by_project: dict[str, dict] = {}
    by_service: dict[str, float] = {}

    for obligation, agreement, project in rows:
        outstanding = float(obligation.amount_due) - float(obligation.amount_received)
        month_key = obligation.due_date.strftime("%Y-%m")
        by_month[month_key] = by_month.get(month_key, 0.0) + outstanding

        project_entry = by_project.setdefault(
            project.project_no, {"projectNo": project.project_no, "projectName": project.project_name, "amount": 0.0}
        )
        project_entry["amount"] += outstanding

        by_service[agreement.stream] = by_service.get(agreement.stream, 0.0) + outstanding

    return {
        "byMonth": [{"month": month, "amount": amount} for month, amount in sorted(by_month.items())],
        "byProject": sorted(by_project.values(), key=lambda entry: entry["projectNo"]),
        "byService": [{"service": service, "amount": amount} for service, amount in sorted(by_service.items())],
    }


def clients_with_projects(db: Session) -> list[dict]:
    """Every non-deleted client alongside every one of their non-deleted
    projects and its current status/stage/progress -- one aggregate query
    plus one grouping pass in Python, rather than the frontend calling
    GET /api/projects?clientId=X once per client (an N+1 request pattern
    that gets slower the more clients exist). Clients with zero projects
    still appear, with an empty projects list, so the report reflects
    every client on file, not just the ones with active work."""
    clients = db.query(Client).filter(Client.deleted_at.is_(None)).order_by(Client.company_name.asc()).all()
    projects = (
        db.query(Project)
        .filter(Project.deleted_at.is_(None))
        .order_by(Project.project_name.asc())
        .all()
    )
    projects_by_client: dict[int, list[Project]] = {}
    for project in projects:
        projects_by_client.setdefault(project.client_id, []).append(project)

    return [
        {
            "clientId": str(client.id),
            "clientName": client.company_name,
            "clientStatus": client.status,
            "projects": [
                {
                    "projectNo": project.project_no,
                    "projectName": project.project_name,
                    "status": project.status,
                    "currentStage": project.current_stage,
                    "progress": project.progress,
                }
                for project in projects_by_client.get(client.id, [])
            ],
        }
        for client in clients
    ]


def project_report(db: Session, project: Project) -> list[dict]:
    task_counts = dict(
        db.query(Task.status, func.count(Task.id))
        .filter(Task.project_id == project.id, Task.deleted_at.is_(None))
        .group_by(Task.status)
        .all()
    )
    document_counts = dict(
        db.query(ProjectDocument.status, func.count(ProjectDocument.id))
        .filter(ProjectDocument.project_id == project.id, ProjectDocument.deleted_at.is_(None))
        .group_by(ProjectDocument.status)
        .all()
    )
    submission_counts = dict(
        db.query(GovernmentSubmission.status, func.count(GovernmentSubmission.id))
        .filter(GovernmentSubmission.project_id == project.id, GovernmentSubmission.deleted_at.is_(None))
        .group_by(GovernmentSubmission.status)
        .all()
    )

    sections = [
        {
            "title": "Project Overview",
            "metrics": [
                {"label": "Status", "value": project.status},
                {"label": "Current Stage", "value": project.current_stage},
                {"label": "Progress", "value": project.progress, "unit": "%"},
                {"label": "Priority", "value": project.priority},
            ],
        },
        {
            "title": "Tasks",
            "metrics": [{"label": status, "value": count} for status, count in task_counts.items()]
            or [{"label": "No tasks recorded", "value": 0}],
        },
        {
            "title": "Documents",
            "metrics": [{"label": status, "value": count} for status, count in document_counts.items()]
            or [{"label": "No documents recorded", "value": 0}],
        },
        {
            "title": "Government Submissions",
            "metrics": [{"label": status, "value": count} for status, count in submission_counts.items()]
            or [{"label": "No submissions recorded", "value": 0}],
        },
    ]

    agreement = (
        db.query(FinancialAgreement)
        .filter(FinancialAgreement.project_id == project.id)
        .order_by(FinancialAgreement.id.desc())
        .first()
    )
    if agreement is not None:
        financial_summary = get_financial_summary(db, agreement.id)
        sections.append(
            {
                "title": "Finance",
                "metrics": [
                    {"label": "Contract Amount", "value": float(agreement.contract_amount), "unit": agreement.currency},
                    {"label": "Total Received", "value": float(financial_summary["totalReceived"]), "unit": agreement.currency},
                    {"label": "Total Pending", "value": float(financial_summary["totalPending"]), "unit": agreement.currency},
                    {"label": "Total Overdue", "value": float(financial_summary["totalOverdue"]), "unit": agreement.currency},
                ],
            }
        )

    return sections
