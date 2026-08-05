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
    completed_projects = (
        db.query(func.count(Project.id))
        .filter(Project.deleted_at.is_(None), Project.status == "Completed")
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
        {"label": "Completed Projects", "value": completed_projects, "color": "info"},
        {"label": "Total Clients", "value": total_clients, "color": "primary"},
        {"label": "Open Tasks", "value": open_tasks, "color": "warning"},
        {"label": "Overdue Tasks", "value": overdue_tasks, "color": "danger"},
        {"label": "Total Received", "value": float(total_received), "unit": "KWD", "color": "success"},
        {"label": "Total Pending", "value": float(total_pending), "unit": "KWD", "color": "warning"},
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
