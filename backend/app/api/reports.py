from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.report import (
    ChartDataPoint,
    ClientWithProjects,
    EmployeePerformance,
    FinancialPeriodSummary,
    PaymentLedgerEntry,
    PaymentProjections,
    PaymentsReceivedByMonth,
    ReportMetric,
    ReportSection,
)
from app.schemas.report_period import ExecutiveSummaryOut, ProjectPerformanceOut, TeamWorkloadOut
from app.services import (
    client_service,
    executive_report_service,
    project_report_service,
    project_service,
    report_service,
    workload_report_service,
)
from app.services.report_period import Period, make_period

router = APIRouter(prefix="/api/reports", tags=["reports"])

can_view = require_permission("Reports", "view")


def period_query(startDate: date, endDate: date) -> Period:
    """?startDate=&endDate= (inclusive Kuwait dates) for any date-ranged report."""
    return make_period(startDate, endDate)


@router.get("/executive", response_model=ExecutiveSummaryOut)
def executive(period: Period = Depends(period_query), db: Session = Depends(get_db), _=Depends(can_view)):
    return executive_report_service.executive_summary(db, period)


@router.get("/project-performance/{project_no}", response_model=ProjectPerformanceOut)
def project_performance(
    project_no: str,
    period: Period = Depends(period_query),
    db: Session = Depends(get_db),
    current_user=Depends(can_view),
):
    project = project_service.get_project(db, project_no)
    # Same freshening as GET /api/projects/{project_no}: this report is
    # often opened for a project whose stage/progress hasn't been
    # recomputed since it last changed.
    project_service.try_auto_advance_stage(db, project, current_user.id)
    project_service.recompute_progress(db, project)
    db.commit()
    db.refresh(project)
    return project_report_service.project_performance(db, project, period)


@router.get("/summary", response_model=list[ReportMetric])
def summary(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.summary_metrics(db)


@router.get("/projects-by-status", response_model=list[ChartDataPoint])
def projects_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.projects_by_status(db)


@router.get("/tasks-by-status", response_model=list[ChartDataPoint])
def tasks_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.tasks_by_status(db)


@router.get("/tasks-by-priority", response_model=list[ChartDataPoint])
def tasks_by_priority(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.tasks_by_priority(db)


@router.get("/submissions-by-status", response_model=list[ChartDataPoint])
def submissions_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.submissions_by_status(db)


@router.get("/quotations-by-status", response_model=list[ChartDataPoint])
def quotations_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.quotations_by_status(db)


@router.get("/contracts-by-status", response_model=list[ChartDataPoint])
def contracts_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.contracts_by_status(db)


@router.get("/documents-by-status", response_model=list[ChartDataPoint])
def documents_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.documents_by_status(db)


@router.get("/payments-received-by-month", response_model=PaymentsReceivedByMonth)
def payments_received_by_month(months: int = 6, db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.payments_received_by_month(db, months)


@router.get("/clients-projects", response_model=list[ClientWithProjects])
def clients_projects(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.clients_with_projects(db)


@router.get("/payment-ledger", response_model=list[PaymentLedgerEntry])
def payment_ledger(
    projectNo: str | None = None,
    clientId: str | None = None,
    startDate: date | None = None,
    endDate: date | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    resolved_client_id = client_service.parse_client_id(clientId) if clientId else None
    return report_service.payment_ledger(db, projectNo, resolved_client_id, startDate, endDate)


@router.get("/payment-projections", response_model=PaymentProjections)
def payment_projections(
    projectNo: str | None = None,
    clientId: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(can_view),
):
    resolved_client_id = client_service.parse_client_id(clientId) if clientId else None
    return report_service.payment_projections(db, projectNo, resolved_client_id)


@router.get("/employee-performance", response_model=list[EmployeePerformance])
def employee_performance(year: int, month: int, db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.employee_performance(db, year, month)


@router.get("/team-workload", response_model=TeamWorkloadOut)
def team_workload(period: Period = Depends(period_query), db: Session = Depends(get_db), _=Depends(can_view)):
    return workload_report_service.team_workload(db, period)


@router.get("/financial-summary", response_model=FinancialPeriodSummary)
def financial_summary(startDate: date, endDate: date, db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.financial_period_summary(db, startDate, endDate)


@router.get("/projects/{project_no}", response_model=list[ReportSection])
def project_report(project_no: str, db: Session = Depends(get_db), current_user=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    # Same self-heal as GET /api/projects/{project_no} (see that
    # endpoint's own comment) -- this report is often the first thing
    # opened for a project that hasn't been viewed through the workspace
    # since its stage/progress last became stale, so it needs the same
    # freshening rather than trusting whatever was last persisted.
    project_service.try_auto_advance_stage(db, project, current_user.id)
    project_service.recompute_progress(db, project)
    db.commit()
    db.refresh(project)
    return report_service.project_report(db, project)
