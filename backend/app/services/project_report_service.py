"""Project Performance: is one project on track, and what happened on it
in a chosen period.

"Today" figures (schedule, open/overdue work, balances) describe where the
project stands now; "in the period" figures (tasks finished, cash
received, instalments that fell due) are counted by their own dates.
Balances use the Payments page's rule (payment_calculations.
get_financial_summary), so the two pages always agree.
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import payment_calculations as calc
from app.core.kuwait_time import kuwait_today
from app.models.client import Client
from app.models.document import ProjectDocument
from app.models.government import GovernmentSubmission
from app.models.payment import FinancialAgreement, Payment, PaymentObligation
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services.report_common import completions, money
from app.services.report_period import Period, bucketer, buckets, granularity, kuwait_date

# Time elapsed may run this many points ahead of progress before the
# project is flagged "at risk".
AT_RISK_GAP_POINTS = 15
# The page shows the first few; the CSV export gets them all (bounded).
OVERDUE_TASKS_LIMIT = 500
UPCOMING_INSTALMENTS_LIMIT = 8


def _schedule(project: Project, today) -> dict:
    total_days = (project.target_date - project.start_date).days
    elapsed_days = min(max((today - project.start_date).days, 0), max(total_days, 0))
    time_elapsed = 100.0 if total_days <= 0 else round(elapsed_days / total_days * 100, 1)
    days_to_target = (project.target_date - today).days
    if project.status in ("Completed", "Cancelled", "On Hold"):
        health = project.status.lower().replace(" ", "-")
    elif days_to_target < 0:
        health = "late"
    elif time_elapsed - project.progress > AT_RISK_GAP_POINTS:
        health = "at-risk"
    else:
        health = "on-track"
    return {
        "startDate": project.start_date.isoformat(),
        "targetDate": project.target_date.isoformat(),
        "totalDays": total_days,
        "timeElapsedPercent": time_elapsed,
        "progressPercent": project.progress,
        "daysToTarget": days_to_target,
        "health": health,
    }


def project_performance(db: Session, project: Project, period: Period) -> dict:
    today = kuwait_today()
    bucket_list = buckets(period)
    index_of = bucketer(bucket_list)

    client_name = db.query(Client.company_name).filter(Client.id == project.client_id).scalar() or ""
    engineer_name = db.query(User.full_name).filter(User.id == project.engineer_id).scalar() or ""

    # ---- Tasks ---------------------------------------------------------------
    live_task = (Task.project_id == project.id, Task.deleted_at.is_(None))
    by_status = dict(db.query(Task.status, func.count(Task.id)).filter(*live_task).group_by(Task.status).all())
    overdue_rows = (
        db.query(Task.task_no, Task.title, Task.due_date, User.full_name)
        .outerjoin(User, User.id == Task.assigned_to)
        .filter(*live_task, Task.status != "Completed", Task.due_date < today)
        .order_by(Task.due_date.asc(), Task.id.asc())
        .all()
    )
    task_ids_due = {task_id for (task_id,) in db.query(Task.id).filter(*live_task, Task.status == "Completed")}
    finished = completions(db, "TASK", period, task_ids_due)
    due_dates = dict(db.query(Task.id, Task.due_date).filter(Task.id.in_(finished.keys()))) if finished else {}
    on_time = sum(1 for task_id, at in finished.items() if kuwait_date(at) <= due_dates[task_id])

    # ---- Money, per billing stream ------------------------------------------
    agreements = (
        db.query(FinancialAgreement).filter(FinancialAgreement.project_id == project.id).order_by(FinancialAgreement.stream).all()
    )
    obligations_by_agreement: dict[int, list] = defaultdict(list)
    if agreements:
        for obligation in db.query(PaymentObligation).filter(
            PaymentObligation.agreement_id.in_([a.id for a in agreements])
        ):
            obligations_by_agreement[obligation.agreement_id].append(obligation)
    received_in_period = dict(
        db.query(Payment.agreement_id, func.sum(Payment.amount_received))
        .filter(Payment.project_id == project.id, Payment.payment_date >= period.start, Payment.payment_date <= period.end)
        .group_by(Payment.agreement_id)
        .all()
    )

    # One chart currency: the project's first agreement's (projects are
    # billed in one currency in practice; others would not add up).
    chart_currency = agreements[0].currency if agreements else None
    received_series = [Decimal("0")] * len(bucket_list)
    billed_series = [Decimal("0")] * len(bucket_list)
    streams = []
    upcoming = []
    for agreement in agreements:
        obligations = obligations_by_agreement[agreement.id]
        summary = calc.get_financial_summary(agreement, obligations)
        billed = Decimal("0")
        for obligation in obligations:
            if obligation.manual_status is None and period.start <= obligation.due_date <= period.end:
                billed += Decimal(str(obligation.amount_due))
                if agreement.currency == chart_currency:
                    billed_series[index_of(obligation.due_date)] += Decimal(str(obligation.amount_due))
            outstanding = calc.get_obligation_amount_pending(obligation)
            if obligation.manual_status is None and outstanding > 0:
                upcoming.append({
                    "stream": agreement.stream,
                    "description": obligation.description,
                    "dueDate": obligation.due_date.isoformat(),
                    "amountDue": money(obligation.amount_due),
                    "outstanding": money(outstanding),
                    "currency": agreement.currency,
                    "overdue": obligation.due_date < today,
                })
        streams.append({
            "stream": agreement.stream,
            "currency": agreement.currency,
            "contractAmount": money(summary["contractAmount"]),
            "received": money(summary["totalReceived"]),
            "outstanding": money(Decimal(str(summary["totalPending"])) + Decimal(str(summary["totalOverdue"]))),
            "overdue": money(summary["totalOverdue"]),
            "receivedInPeriod": money(received_in_period.get(agreement.id)),
            "billedInPeriod": money(billed),
        })
    if chart_currency:
        for payment_date, amount in (
            db.query(Payment.payment_date, Payment.amount_received)
            .join(FinancialAgreement, FinancialAgreement.id == Payment.agreement_id)
            .filter(
                Payment.project_id == project.id,
                FinancialAgreement.currency == chart_currency,
                Payment.payment_date >= period.start,
                Payment.payment_date <= period.end,
            )
        ):
            received_series[index_of(payment_date)] += Decimal(str(amount))
    upcoming.sort(key=lambda row: row["dueDate"])

    documents = (
        db.query(ProjectDocument.status, func.count(ProjectDocument.id))
        .filter(ProjectDocument.project_id == project.id, ProjectDocument.deleted_at.is_(None))
        .group_by(ProjectDocument.status)
        .all()
    )
    submissions = (
        db.query(GovernmentSubmission.stage, func.count(GovernmentSubmission.id))
        .filter(GovernmentSubmission.project_id == project.id, GovernmentSubmission.deleted_at.is_(None))
        .group_by(GovernmentSubmission.stage)
        .all()
    )

    open_tasks = sum(count for status, count in by_status.items() if status != "Completed")
    return {
        "period": period.as_dict(),
        "bucket": granularity(period),
        "project": {
            "projectNo": project.project_no,
            "projectName": project.project_name,
            "clientName": client_name,
            "engineer": engineer_name,
            "status": project.status,
            "currentStage": project.current_stage,
        },
        "schedule": _schedule(project, today),
        "tasks": {
            "byStatus": [{"label": status, "value": count} for status, count in sorted(by_status.items(), key=lambda row: -row[1])],
            "total": sum(by_status.values()),
            "open": open_tasks,
            "overdue": len(overdue_rows),
            "completedInPeriod": len(finished),
            "onTimeRate": round(on_time / len(finished) * 100, 1) if finished else None,
            "overdueList": [
                {"taskNo": no, "title": title, "assignee": assignee or "", "dueDate": due.isoformat(), "daysLate": (today - due).days}
                for no, title, due, assignee in overdue_rows[:OVERDUE_TASKS_LIMIT]
            ],
        },
        "money": {
            "streams": streams,
            "chartCurrency": chart_currency,
            "cashFlow": {
                "categories": [bucket.label for bucket in bucket_list],
                "received": [money(v) for v in received_series],
                "billed": [money(v) for v in billed_series],
            },
            "upcoming": upcoming[:UPCOMING_INSTALMENTS_LIMIT],
        },
        "documents": [{"label": status, "value": count} for status, count in documents],
        "submissions": [{"label": stage, "value": count} for stage, count in submissions],
    }
