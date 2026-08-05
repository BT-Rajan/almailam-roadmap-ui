from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.report import ChartDataPoint, LineChartDataPoint, ReportMetric, ReportSection
from app.services import project_service, report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])

can_view = require_permission("Reports", "view")


@router.get("/summary", response_model=list[ReportMetric])
def summary(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.summary_metrics(db)


@router.get("/projects-by-status", response_model=list[ChartDataPoint])
def projects_by_status(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.projects_by_status(db)


@router.get("/projects-by-priority", response_model=list[ChartDataPoint])
def projects_by_priority(db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.projects_by_priority(db)


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


@router.get("/payments-received-by-month", response_model=list[LineChartDataPoint])
def payments_received_by_month(months: int = 6, db: Session = Depends(get_db), _=Depends(can_view)):
    return report_service.payments_received_by_month(db, months)


@router.get("/projects/{project_no}", response_model=list[ReportSection])
def project_report(project_no: str, db: Session = Depends(get_db), _=Depends(can_view)):
    project = project_service.get_project(db, project_no)
    return report_service.project_report(db, project)
