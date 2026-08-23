from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.status_report import EngineerProjectOption, StatusReportFileRequest, StatusReportOut
from app.services import status_report_service

router = APIRouter(prefix="/api/site-portal", tags=["site-portal"])


def _report_out(db: Session, report) -> StatusReportOut:
    project = db.query(Project).filter(Project.id == report.project_id).first()
    engineer = db.query(User).filter(User.id == report.engineer_id).first()
    attached_by = db.query(User).filter(User.id == report.attached_by).first() if report.attached_by else None
    attached_task = None
    if report.attached_task_id:
        from app.models.task import Task
        attached_task = db.query(Task).filter(Task.id == report.attached_task_id).first()

    return StatusReportOut.from_model(
        report,
        project.project_no if project else "",
        project.project_name if project else "Unknown Project",
        engineer.full_name if engineer else "Unknown",
        attached_by.full_name if attached_by else None,
        attached_task.task_no if attached_task else None,
    )


@router.get("/projects", response_model=list[EngineerProjectOption])
def list_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = status_report_service.list_engineer_projects(db, current_user.id)
    return [EngineerProjectOption(id=p.project_no, projectName=p.project_name) for p in projects]


@router.get("/reports/today", response_model=list[StatusReportOut])
def list_todays_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Every report this engineer has already filed today, one per
    project -- an engineer on multiple projects sees, per project,
    whether today's report is filed yet. The frontend cross-references
    this against /projects to know which are still outstanding."""
    reports = status_report_service.list_todays_reports(db, current_user.id)
    return [_report_out(db, r) for r in reports]


@router.post("/reports/today", response_model=StatusReportOut)
def file_todays_report(
    payload: StatusReportFileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = status_report_service.file_todays_report(
        db, current_user.id, payload.projectId, payload.receiptType, payload.supervisionType, payload.notes
    )
    return _report_out(db, report)


@router.get("/reports", response_model=list[StatusReportOut])
def list_my_reports(
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = status_report_service.list_reports_for_engineer(db, current_user.id, start, end)
    return [_report_out(db, r) for r in reports]
