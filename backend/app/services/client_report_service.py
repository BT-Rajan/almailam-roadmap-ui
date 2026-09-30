"""Client Projects: for every client, where their projects stand, what
they paid in a chosen period, and what they still owe.

Money is in the company's configured currency only (other-currency
agreements would not add up) and uses the Payments page's rule: an
instalment's live amount due minus amount received, cancelled/waived
instalments excluded, overdue once its due date has passed.
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.kuwait_time import kuwait_today
from app.models.client import Client
from app.models.payment import FinancialAgreement, Payment, PaymentObligation
from app.models.project import Project
from app.services import company_service
from app.services.report_common import money
from app.services.report_period import Period

PROJECT_STATUSES = ("Active", "On Hold", "Completed", "Cancelled")


def client_portfolio(db: Session, period: Period) -> dict:
    today = kuwait_today()
    currency = company_service.get_settings(db).currency

    clients = db.query(Client).filter(Client.deleted_at.is_(None)).order_by(Client.company_name.asc()).all()
    project_rows = (
        db.query(
            Project.id, Project.client_id, Project.project_no, Project.project_name, Project.status,
            Project.current_stage, Project.progress, Project.created_at,
        )
        .filter(Project.deleted_at.is_(None))
        .order_by(Project.project_name.asc())
        .all()
    )

    unpaid = PaymentObligation.amount_due > PaymentObligation.amount_received
    balance = PaymentObligation.amount_due - PaymentObligation.amount_received
    owed = {
        project_id: (outstanding, overdue)
        for project_id, outstanding, overdue in db.query(
            FinancialAgreement.project_id,
            func.sum(case((unpaid, balance), else_=0)),
            func.sum(case((unpaid & (PaymentObligation.due_date < today), balance), else_=0)),
        )
        .join(FinancialAgreement, FinancialAgreement.id == PaymentObligation.agreement_id)
        .filter(FinancialAgreement.currency == currency, PaymentObligation.manual_status.is_(None))
        .group_by(FinancialAgreement.project_id)
    }
    received = dict(
        db.query(Payment.project_id, func.sum(Payment.amount_received))
        .join(FinancialAgreement, FinancialAgreement.id == Payment.agreement_id)
        .filter(FinancialAgreement.currency == currency, Payment.payment_date >= period.start, Payment.payment_date <= period.end)
        .group_by(Payment.project_id)
        .all()
    )

    projects_by_client: dict[int, list[dict]] = defaultdict(list)
    for project_id, client_id, project_no, name, status, stage, progress, created_at in project_rows:
        outstanding, overdue = owed.get(project_id, (0, 0))
        projects_by_client[client_id].append({
            "projectNo": project_no,
            "projectName": name,
            "status": status,
            "currentStage": stage,
            "progress": progress,
            "newInPeriod": period.utc_start <= created_at < period.utc_end_exclusive,
            "receivedInPeriod": money(received.get(project_id)),
            "outstanding": money(outstanding),
            "overdue": money(overdue),
        })

    rows = []
    for client in clients:
        projects = projects_by_client.get(client.id, [])
        status_counts = {status: sum(1 for p in projects if p["status"] == status) for status in PROJECT_STATUSES}
        rows.append({
            "clientId": f"CLT-{client.id:03d}",
            "clientName": client.company_name,
            "clientStatus": client.status,
            "newClient": period.utc_start <= client.created_at < period.utc_end_exclusive,
            "totalProjects": len(projects),
            "activeProjects": status_counts["Active"],
            "onHoldProjects": status_counts["On Hold"],
            "completedProjects": status_counts["Completed"],
            "cancelledProjects": status_counts["Cancelled"],
            "newProjectsInPeriod": sum(1 for p in projects if p["newInPeriod"]),
            "receivedInPeriod": money(sum((Decimal(str(p["receivedInPeriod"])) for p in projects), Decimal("0"))),
            "outstanding": money(sum((Decimal(str(p["outstanding"])) for p in projects), Decimal("0"))),
            "overdue": money(sum((Decimal(str(p["overdue"])) for p in projects), Decimal("0"))),
            "projects": projects,
        })

    return {
        "period": period.as_dict(),
        "currency": currency,
        "totals": {
            "clients": len(rows),
            "clientsWithActiveWork": sum(1 for row in rows if row["activeProjects"]),
            "newClients": sum(1 for row in rows if row["newClient"]),
            "clientsWithoutProjects": sum(1 for row in rows if not row["totalProjects"]),
            "projects": sum(row["totalProjects"] for row in rows),
            "newProjects": sum(row["newProjectsInPeriod"] for row in rows),
            "receivedInPeriod": money(sum((Decimal(str(row["receivedInPeriod"])) for row in rows), Decimal("0"))),
            "outstanding": money(sum((Decimal(str(row["outstanding"])) for row in rows), Decimal("0"))),
            "overdue": money(sum((Decimal(str(row["overdue"])) for row in rows), Decimal("0"))),
            "clientsWithOverdue": sum(1 for row in rows if row["overdue"] > 0),
        },
        "clients": rows,
    }
