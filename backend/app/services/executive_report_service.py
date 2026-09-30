"""Executive Summary: how the business did over a chosen period.

Everything "in the period" is a flow (work won, work finished, money in,
money billed) counted by its own date; everything "now" is a position as
of today (what is still owed, what is late). Money is in the company's
configured currency only -- adding AED to USD would be meaningless -- and
uses the same rules as the Payments page (an obligation's live amount due
minus amount received; cancelled/waived obligations excluded).
"""

from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.kuwait_time import kuwait_today
from app.models.client import Client
from app.models.contract import Contract
from app.models.payment import FinancialAgreement, Payment, PaymentObligation, Refund
from app.models.project import Project
from app.models.task import Task
from app.services import company_service
from app.services.report_common import completions as _completions
from app.services.report_common import money as _money
from app.services.report_period import Period, bucketer, buckets, granularity, kuwait_date

TOP_CLIENTS_LIMIT = 10
SIGNED_CONTRACT_STATUSES = ("Signed", "Active", "Expired", "Terminated")


def executive_summary(db: Session, period: Period) -> dict:
    today = kuwait_today()
    currency = company_service.get_settings(db).currency
    bucket_list = buckets(period)
    index_of = bucketer(bucket_list)
    categories = [bucket.label for bucket in bucket_list]

    # ---- Projects: won, finished, and where they stand now ----------------
    live_project = Project.deleted_at.is_(None)
    started = [0] * len(bucket_list)
    new_projects = db.query(Project.created_at).filter(
        live_project, Project.created_at >= period.utc_start, Project.created_at < period.utc_end_exclusive
    ).all()
    for (created_at,) in new_projects:
        index = index_of(kuwait_date(created_at))
        if index is not None:
            started[index] += 1

    completed = [0] * len(bucket_list)
    project_completions = _completions(db, "PROJECT", period)
    still_completed = (
        {
            project_id
            for (project_id,) in db.query(Project.id).filter(
                live_project, Project.status == "Completed", Project.id.in_(project_completions.keys())
            )
        }
        if project_completions
        else set()
    )
    for project_id in still_completed:
        index = index_of(kuwait_date(project_completions[project_id]))
        if index is not None:
            completed[index] += 1

    status_rows = db.query(Project.status, func.count(Project.id)).filter(live_project).group_by(Project.status).all()
    status_counts = dict(status_rows)

    new_clients = (
        db.query(func.count(Client.id))
        .filter(Client.deleted_at.is_(None), Client.created_at >= period.utc_start, Client.created_at < period.utc_end_exclusive)
        .scalar()
        or 0
    )

    contracts_signed, contracts_value = (
        db.query(func.count(Contract.id), func.coalesce(func.sum(Contract.contract_value), 0))
        .join(Project, Project.id == Contract.project_id)
        .filter(
            Contract.deleted_at.is_(None),
            live_project,
            Contract.status.in_(SIGNED_CONTRACT_STATUSES),
            Contract.currency == currency,
            Contract.signed_date >= period.start,
            Contract.signed_date <= period.end,
        )
        .one()
    )

    # ---- Money in the period ----------------------------------------------
    in_currency = FinancialAgreement.currency == currency
    received = [Decimal("0")] * len(bucket_list)
    for payment_date, amount in (
        db.query(Payment.payment_date, Payment.amount_received)
        .join(FinancialAgreement, FinancialAgreement.id == Payment.agreement_id)
        .filter(in_currency, Payment.payment_date >= period.start, Payment.payment_date <= period.end)
    ):
        index = index_of(payment_date)
        if index is not None:
            received[index] += Decimal(str(amount))

    refunded = (
        db.query(func.coalesce(func.sum(Refund.refund_amount), 0))
        .join(FinancialAgreement, FinancialAgreement.id == Refund.agreement_id)
        .filter(in_currency, Refund.refund_date >= period.start, Refund.refund_date <= period.end)
        .scalar()
    )

    billed = [Decimal("0")] * len(bucket_list)
    billed_total = collected_of_billed = Decimal("0")
    for due_date, amount_due, amount_received in (
        db.query(PaymentObligation.due_date, PaymentObligation.amount_due, PaymentObligation.amount_received)
        .join(FinancialAgreement, FinancialAgreement.id == PaymentObligation.agreement_id)
        .filter(
            in_currency,
            PaymentObligation.manual_status.is_(None),
            PaymentObligation.due_date >= period.start,
            PaymentObligation.due_date <= period.end,
        )
    ):
        due, got = Decimal(str(amount_due)), Decimal(str(amount_received))
        billed_total += due
        collected_of_billed += min(got, due)
        index = index_of(due_date)
        if index is not None:
            billed[index] += due

    # ---- Money position today (same rule as the Payments page) -------------
    unpaid = PaymentObligation.amount_due > PaymentObligation.amount_received
    balance = PaymentObligation.amount_due - PaymentObligation.amount_received
    outstanding_now, overdue_now = (
        db.query(
            func.coalesce(func.sum(case((unpaid, balance), else_=0)), 0),
            func.coalesce(func.sum(case((unpaid & (PaymentObligation.due_date < today), balance), else_=0)), 0),
        )
        .join(FinancialAgreement, FinancialAgreement.id == PaymentObligation.agreement_id)
        .filter(in_currency, PaymentObligation.manual_status.is_(None))
        .one()
    )

    top_clients = (
        db.query(Client.company_name, func.sum(Payment.amount_received), func.count(Payment.id))
        .join(Project, Project.id == Payment.project_id)
        .join(Client, Client.id == Project.client_id)
        .join(FinancialAgreement, FinancialAgreement.id == Payment.agreement_id)
        .filter(in_currency, Payment.payment_date >= period.start, Payment.payment_date <= period.end)
        .group_by(Client.id, Client.company_name)
        .order_by(func.sum(Payment.amount_received).desc())
        .limit(TOP_CLIENTS_LIMIT)
        .all()
    )

    # ---- Delivery ------------------------------------------------------------
    task_completions = _completions(db, "TASK", period)
    tasks_completed = on_time = 0
    if task_completions:
        for task_id, due_date in db.query(Task.id, Task.due_date).filter(
            Task.deleted_at.is_(None), Task.status == "Completed", Task.id.in_(task_completions.keys())
        ):
            tasks_completed += 1
            if kuwait_date(task_completions[task_id]) <= due_date:
                on_time += 1
    open_task = (Task.deleted_at.is_(None), Task.status != "Completed")
    open_tasks, overdue_tasks = db.query(
        func.count(Task.id), func.coalesce(func.sum(case((Task.due_date < today, 1), else_=0)), 0)
    ).filter(*open_task).one()

    received_total = sum(received, Decimal("0"))
    return {
        "period": period.as_dict(),
        "bucket": granularity(period),
        "currency": currency,
        "kpis": {
            "newProjects": len(new_projects),
            "projectsCompleted": len(still_completed),
            "activeProjectsNow": status_counts.get("Active", 0),
            "onHoldProjectsNow": status_counts.get("On Hold", 0),
            "newClients": new_clients,
            "contractsSigned": contracts_signed,
            "contractsSignedValue": _money(contracts_value),
            "cashReceived": _money(received_total),
            "refunded": _money(refunded),
            "netCash": _money(received_total - Decimal(str(refunded or 0))),
            "billed": _money(billed_total),
            "collectedOfBilled": _money(collected_of_billed),
            "collectionRate": round(float(collected_of_billed / billed_total * 100), 1) if billed_total else None,
            "outstandingNow": _money(outstanding_now),
            "overdueNow": _money(overdue_now),
            "tasksCompleted": tasks_completed,
            "tasksOnTimeRate": round(on_time / tasks_completed * 100, 1) if tasks_completed else None,
            "openTasksNow": open_tasks,
            "overdueTasksNow": int(overdue_tasks),
        },
        "cashFlow": {"categories": categories, "received": [_money(v) for v in received], "billed": [_money(v) for v in billed]},
        "projectFlow": {"categories": categories, "started": started, "completed": completed},
        "projectStatusNow": [
            {"label": status, "value": count} for status, count in sorted(status_rows, key=lambda row: -row[1])
        ],
        "topClients": [
            {"clientName": name, "received": _money(total), "payments": count} for name, total, count in top_clients
        ],
    }
