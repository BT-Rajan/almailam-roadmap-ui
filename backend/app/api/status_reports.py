from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.status_report import StatusReportAttachRequest, StatusReportOut
from app.services import company_service, status_report_service

router = APIRouter(prefix="/api/status-reports", tags=["status-reports"])


def _require_recipient_or_admin(db: Session, current_user: User) -> None:
    """The inbox and attach action are only for whoever CompanySettings.
    status_report_recipient_id is currently set to, plus Administrators
    as a standing override -- not a general permission-matrix entry,
    since this is a single named person's queue, not a role-wide
    capability."""
    if current_user.role == "Administrator":
        return
    settings = company_service.get_settings(db)
    if settings.status_report_recipient_id != current_user.id:
        raise PermissionDeniedError()


def _report_out(db: Session, report) -> StatusReportOut:
    project = db.query(Project).filter(Project.id == report.project_id).first()
    engineer = db.query(User).filter(User.id == report.engineer_id).first()
    attached_by = db.query(User).filter(User.id == report.attached_by).first() if report.attached_by else None
    attached_task = db.query(Task).filter(Task.id == report.attached_task_id).first() if report.attached_task_id else None

    return StatusReportOut.from_model(
        report,
        project.project_no if project else "",
        project.project_name if project else "Unknown Project",
        engineer.full_name if engineer else "Unknown",
        attached_by.full_name if attached_by else None,
        attached_task.task_no if attached_task else None,
    )


@router.get("/inbox", response_model=list[StatusReportOut])
def list_inbox(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_recipient_or_admin(db, current_user)
    reports = status_report_service.list_inbox(db)
    return [_report_out(db, r) for r in reports]


@router.post("/{report_id}/attach", response_model=StatusReportOut)
def attach_report(
    report_id: int,
    payload: StatusReportAttachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_recipient_or_admin(db, current_user)
    report = status_report_service.attach_report(db, report_id, payload.taskId, payload.notes, current_user.id)
    return _report_out(db, report)
