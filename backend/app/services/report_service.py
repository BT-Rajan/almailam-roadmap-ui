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
from app.models.user import User
from app.services import company_service
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
    """Payments received per month, scoped to the company's configured
    default currency (see CompanySettings.currency / AdminCompanyPage) --
    FinancialAgreement.currency is picked per contract/quotation (AED/
    USD/SAR/KWD, see AgreementFormDialog/NewContractDialog), so summing
    every Payment regardless of its agreement's currency would silently
    add different currencies together. A single trend line can only
    honestly represent one currency at a time; if other currencies are
    in use, this is the org's default one, not necessarily "all of it"."""
    today = date.today()
    year, month = today.year, today.month
    buckets: list[tuple[int, int]] = []
    for _ in range(months):
        buckets.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    buckets.reverse()

    report_currency = company_service.get_settings(db).currency
    rows = (
        db.query(
            func.year(Payment.payment_date),
            func.month(Payment.payment_date),
            func.sum(Payment.amount_received),
        )
        .join(FinancialAgreement, Payment.agreement_id == FinancialAgreement.id)
        .filter(FinancialAgreement.currency == report_currency)
        .group_by(func.year(Payment.payment_date), func.month(Payment.payment_date))
        .all()
    )
    totals = {(int(y), int(m)): float(total) for y, m, total in rows}

    return {
        "currency": report_currency,
        "series": [{"x": f"{month_abbr[m]} {y}", "value": totals.get((y, m), 0.0)} for y, m in buckets],
    }


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
    # Total Received / Total Pending, broken out by currency. Obligations
    # aren't guaranteed to share one currency -- FinancialAgreement.currency
    # is picked per contract/quotation (AED/USD/SAR/KWD, see
    # AgreementFormDialog/NewContractDialog/company_service's own default
    # of "AED") -- so a single unlabeled sum would silently add different
    # currencies together. Emit one metric per currency actually present;
    # only fall back to the company's configured default when there's no
    # payment data at all yet, so the cards aren't just missing.
    received_by_currency = dict(
        db.query(FinancialAgreement.currency, func.sum(PaymentObligation.amount_received))
        .join(FinancialAgreement, PaymentObligation.agreement_id == FinancialAgreement.id)
        .group_by(FinancialAgreement.currency)
        .all()
    )
    pending_by_currency = dict(
        db.query(FinancialAgreement.currency, func.sum(PaymentObligation.amount_due - PaymentObligation.amount_received))
        .join(FinancialAgreement, PaymentObligation.agreement_id == FinancialAgreement.id)
        .filter(PaymentObligation.manual_status.is_(None))
        .group_by(FinancialAgreement.currency)
        .all()
    )
    currencies = sorted(set(received_by_currency) | set(pending_by_currency)) or [company_service.get_settings(db).currency]
    multi_currency = len(currencies) > 1

    metrics = [
        {"label": "Total Projects", "value": total_projects, "color": "primary"},
        {"label": "Active Projects", "value": active_projects, "color": "success"},
        {"label": "On Hold Projects", "value": on_hold_projects, "color": "info"},
        {"label": "Total Clients", "value": total_clients, "color": "primary"},
        {"label": "Open Tasks", "value": open_tasks, "color": "warning"},
        {"label": "Overdue Tasks", "value": overdue_tasks, "color": "danger"},
    ]
    for currency in currencies:
        label = f"Total Received ({currency})" if multi_currency else "Total Received"
        metrics.append(
            {"label": label, "value": float(received_by_currency.get(currency, 0) or 0), "unit": currency, "color": "success"}
        )
    for currency in currencies:
        label = f"Total Pending ({currency})" if multi_currency else "Total Pending"
        metrics.append(
            {"label": label, "value": float(pending_by_currency.get(currency, 0) or 0), "unit": currency, "color": "warning"}
        )
    return metrics


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
    without three separate round trips. Each grouping also splits by
    FinancialAgreement.currency: a project can hold a Design agreement
    and a Supervision agreement in different currencies (nothing in the
    schema ties them together), and even within one stream, obligations
    across different projects/clients can genuinely be priced in
    different currencies (AED/USD/SAR/KWD -- see AdminCompanyPage).
    Summing across currencies into one number, the way this used to
    work, would silently add incompatible amounts together."""
    rows = _outstanding_obligations_query(db, project_no, client_id).all()

    by_month: dict[tuple[str, str], float] = {}
    by_project: dict[tuple[str, str], dict] = {}
    by_service: dict[tuple[str, str], float] = {}

    for obligation, agreement, project in rows:
        outstanding = float(obligation.amount_due) - float(obligation.amount_received)
        currency = agreement.currency
        month_key = obligation.due_date.strftime("%Y-%m")
        by_month[(month_key, currency)] = by_month.get((month_key, currency), 0.0) + outstanding

        project_key = (project.project_no, currency)
        project_entry = by_project.setdefault(
            project_key,
            {"projectNo": project.project_no, "projectName": project.project_name, "currency": currency, "amount": 0.0},
        )
        project_entry["amount"] += outstanding

        service_key = (agreement.stream, currency)
        by_service[service_key] = by_service.get(service_key, 0.0) + outstanding

    return {
        "byMonth": [
            {"month": month, "currency": currency, "amount": amount}
            for (month, currency), amount in sorted(by_month.items())
        ],
        "byProject": sorted(by_project.values(), key=lambda entry: (entry["projectNo"], entry["currency"])),
        "byService": [
            {"service": service, "currency": currency, "amount": amount}
            for (service, currency), amount in sorted(by_service.items())
        ],
    }


def employee_performance(db: Session, year: int, month: int) -> list[dict]:
    """Assigned-vs-completed task counts per employee for one calendar
    month -- "assigned" is every non-deleted task due that month
    currently assigned to them (their workload for the month, regardless
    of when it was created or who it's since been reassigned to/from),
    "completed" is the subset of those specific tasks that are actually
    Completed. Only employees with at least one task due in the month
    appear -- there's nothing to report for someone with zero workload
    that month."""
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    rows = (
        db.query(Task.assigned_to, Task.status, func.count(Task.id))
        .filter(Task.deleted_at.is_(None), Task.due_date >= start, Task.due_date < end)
        .group_by(Task.assigned_to, Task.status)
        .all()
    )

    by_user: dict[int, dict[str, int]] = {}
    for assigned_to, status, count in rows:
        entry = by_user.setdefault(assigned_to, {"assigned": 0, "completed": 0})
        entry["assigned"] += count
        if status == "Completed":
            entry["completed"] += count

    user_ids = list(by_user.keys())
    names = (
        {u.id: u.full_name for u in db.query(User.id, User.full_name).filter(User.id.in_(user_ids)).all()}
        if user_ids
        else {}
    )

    results = [
        {
            "userId": str(user_id),
            "employeeName": names.get(user_id, "Unknown"),
            "assigned": data["assigned"],
            "completed": data["completed"],
            "completionRate": round(data["completed"] * 100 / data["assigned"]) if data["assigned"] else 0,
        }
        for user_id, data in by_user.items()
    ]
    return sorted(results, key=lambda entry: entry["employeeName"])


# No table anywhere tracks a person's actual capacity (hours/week,
# FTE, or anything similar) -- User has no such column, and Task has no
# estimate/effort field either (see models/user.py, models/task.py). So
# "how full is this person" can't be measured, only approximated from
# what we do track: how many tasks are currently open on them. This
# constant is that approximation's one free parameter -- the open-task
# count treated as "fully loaded" for allocation-percent purposes. It's
# a business assumption, not a measured figure, and should be revisited
# (or the whole allocationPercent field dropped) if it doesn't match
# how the team actually thinks about workload.
TASKS_AT_FULL_CAPACITY = 8


def team_workload(db: Session) -> dict:
    """Real per-engineer workload: currently-open task count, overdue
    task count, and active (status='Active') project count, each read
    straight from tasks/projects -- no discipline/department breakdown,
    since no such field exists on User; role is the only real
    grouping available. allocationPercent is open tasks against
    TASKS_AT_FULL_CAPACITY above, not a measured utilization figure.
    Only active, non-deleted Engineers are included -- they're the
    role tasks/projects actually get assigned to (see
    core.permissions.ROLES and Project.engineer_id)."""
    engineers = (
        db.query(User)
        .filter(User.role == "Engineer", User.is_active.is_(True), User.deleted_at.is_(None))
        .all()
    )
    if not engineers:
        return {
            "members": [],
            "totalMembers": 0,
            "averageUtilization": 0,
            "overallocatedCount": 0,
            "capacityAvailable": 0,
        }

    engineer_ids = [engineer.id for engineer in engineers]
    today = date.today()

    open_tasks_by_user = dict(
        db.query(Task.assigned_to, func.count(Task.id))
        .filter(Task.deleted_at.is_(None), Task.status != "Completed", Task.assigned_to.in_(engineer_ids))
        .group_by(Task.assigned_to)
        .all()
    )
    overdue_by_user = dict(
        db.query(Task.assigned_to, func.count(Task.id))
        .filter(
            Task.deleted_at.is_(None),
            Task.status != "Completed",
            Task.due_date < today,
            Task.assigned_to.in_(engineer_ids),
        )
        .group_by(Task.assigned_to)
        .all()
    )
    active_projects_by_user = dict(
        db.query(Project.engineer_id, func.count(Project.id))
        .filter(Project.deleted_at.is_(None), Project.status == "Active", Project.engineer_id.in_(engineer_ids))
        .group_by(Project.engineer_id)
        .all()
    )

    members = []
    for engineer in engineers:
        open_tasks = open_tasks_by_user.get(engineer.id, 0)
        allocation_percent = round(open_tasks * 100 / TASKS_AT_FULL_CAPACITY)
        members.append(
            {
                "userId": str(engineer.id),
                "name": engineer.full_name,
                "role": engineer.role,
                "activeProjects": active_projects_by_user.get(engineer.id, 0),
                "activeTasks": open_tasks,
                "overdueTasks": overdue_by_user.get(engineer.id, 0),
                "allocationPercent": allocation_percent,
                "overallocated": allocation_percent > 100,
            }
        )
    members.sort(key=lambda member: member["name"])

    average_utilization = round(sum(member["allocationPercent"] for member in members) / len(members))
    overallocated_count = sum(1 for member in members if member["overallocated"])

    return {
        "members": members,
        "totalMembers": len(members),
        "averageUtilization": average_utilization,
        "overallocatedCount": overallocated_count,
        "capacityAvailable": max(0, 100 - average_utilization),
    }


def financial_period_summary(db: Session, start_date: date, end_date: date) -> dict:
    """One period's financial snapshot -- total received (payments
    recorded in the period), total due (obligations that fell due in the
    period, regardless of whether they were paid), and how much of that
    billing is still outstanding/overdue as of today. Both bounds are
    inclusive (unlike activity_service's exclusive-end convention) --
    callers pass a calendar period's actual first/last day directly, no
    "day after" adjustment needed. Meant to be called twice (once for
    the period being looked at, once for whatever it's being compared
    against) and diffed by the caller -- kept as a single-period query
    rather than baking the comparison in here, so it stays reusable for
    anything else that just wants "how did we do in period X".

    Every total is broken out by currency (FinancialAgreement.currency)
    rather than summed together: a single project can hold agreements
    in different currencies (Design vs Supervision), so a flat sum
    would silently add incompatible amounts. paymentCount is the one
    exception -- a raw count of Payment rows is meaningful regardless
    of what currency each payment happened to be in, so it stays a
    single top-level figure rather than being split too."""
    received_by_currency: dict[str, float] = {}
    for currency, total in (
        db.query(FinancialAgreement.currency, func.sum(Payment.amount_received))
        .join(FinancialAgreement, Payment.agreement_id == FinancialAgreement.id)
        .filter(Payment.payment_date >= start_date, Payment.payment_date <= end_date)
        .group_by(FinancialAgreement.currency)
        .all()
    ):
        received_by_currency[currency] = float(total or 0)

    payment_count = (
        db.query(func.count(Payment.id))
        .filter(Payment.payment_date >= start_date, Payment.payment_date <= end_date)
        .scalar()
        or 0
    )
    obligations_due = (
        db.query(PaymentObligation, FinancialAgreement)
        .join(FinancialAgreement, PaymentObligation.agreement_id == FinancialAgreement.id)
        .filter(PaymentObligation.due_date >= start_date, PaymentObligation.due_date <= end_date)
        .all()
    )
    today = date.today()
    due_by_currency: dict[str, float] = {}
    outstanding_by_currency: dict[str, float] = {}
    overdue_by_currency: dict[str, float] = {}
    for obligation, agreement in obligations_due:
        currency = agreement.currency
        due_amount = float(obligation.amount_due)
        due_by_currency[currency] = due_by_currency.get(currency, 0.0) + due_amount
        if obligation.manual_status is not None:
            continue
        remaining = max(due_amount - float(obligation.amount_received), 0.0)
        outstanding_by_currency[currency] = outstanding_by_currency.get(currency, 0.0) + remaining
        if remaining > 0 and obligation.due_date < today:
            overdue_by_currency[currency] = overdue_by_currency.get(currency, 0.0) + remaining

    currencies = sorted(
        set(received_by_currency) | set(due_by_currency) | set(outstanding_by_currency) | set(overdue_by_currency)
    ) or [company_service.get_settings(db).currency]

    return {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "paymentCount": payment_count,
        "byCurrency": [
            {
                "currency": currency,
                "totalReceived": received_by_currency.get(currency, 0.0),
                "totalDue": due_by_currency.get(currency, 0.0),
                "totalOutstanding": outstanding_by_currency.get(currency, 0.0),
                "totalOverdue": overdue_by_currency.get(currency, 0.0),
            }
            for currency in currencies
        ],
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

    # A project can have up to one agreement PER billing stream (Design,
    # Supervision -- see the (project_id, stream) unique constraint on
    # FinancialAgreement, and ProjectOverviewTab.vue's own "one row per
    # stream this project actually includes" handling). Picking only the
    # single latest-by-id agreement here used to silently drop whichever
    # stream wasn't picked when a project has both -- e.g. a project with
    # a Supervision agreement added after its Design one would show only
    # Supervision's numbers and lose Design's Contract Amount/Received/
    # Pending/Overdue entirely. Now emits one Finance section per
    # agreement that actually exists, ordered by stream name so Design
    # (if present) shows before Supervision.
    agreements = (
        db.query(FinancialAgreement)
        .filter(FinancialAgreement.project_id == project.id)
        .order_by(FinancialAgreement.stream)
        .all()
    )
    multi_stream = len(agreements) > 1
    for agreement in agreements:
        financial_summary = get_financial_summary(db, agreement.id)
        title = f"Finance ({agreement.stream})" if multi_stream else "Finance"
        sections.append(
            {
                "title": title,
                "metrics": [
                    {"label": "Contract Amount", "value": float(agreement.contract_amount), "unit": agreement.currency},
                    {"label": "Total Received", "value": float(financial_summary["totalReceived"]), "unit": agreement.currency},
                    {"label": "Total Pending", "value": float(financial_summary["totalPending"]), "unit": agreement.currency},
                    {"label": "Total Overdue", "value": float(financial_summary["totalOverdue"]), "unit": agreement.currency},
                ],
            }
        )

    return sections
