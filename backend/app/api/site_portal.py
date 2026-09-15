from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.file_storage import resolve_path
from app.models.project import Project
from app.models.status_report import StatusReportImage
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
        status_report_service.list_report_images(db, report.id),
    )


@router.get("/projects", response_model=list[EngineerProjectOption])
def list_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = status_report_service.list_engineer_projects(db, current_user.id)
    today = status_report_service.report_filing_today(db)

    def _to_option(p: Project) -> EngineerProjectOption:
        reason = status_report_service.filing_window_block_reason(p, today)
        return EngineerProjectOption(id=p.project_no, projectName=p.project_name, canFileReport=reason is None, blockReason=reason)

    return [_to_option(p) for p in projects]


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


@router.post("/reports/{report_id}/images", response_model=StatusReportOut)
async def upload_report_image(
    report_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = status_report_service.add_report_image(db, report_id, current_user.id, file)
    return _report_out(db, report)


@router.delete("/reports/{report_id}/images/{image_id}", response_model=StatusReportOut)
def delete_report_image(
    report_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = status_report_service.delete_report_image(db, report_id, current_user.id, image_id)
    return _report_out(db, report)


@router.get("/reports/{report_id}/images/{image_id}/file")
def download_report_image(
    report_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    # Not restricted to the filing engineer, unlike upload/delete above --
    # office staff reviewing the inbox (status_reports.py's own endpoints)
    # need to actually view these photos too, and there isn't a separate
    # download route registered there. Any authenticated user, same as
    # every other GET on this router.
    _current_user: User = Depends(get_current_user),
):
    image = (
        db.query(StatusReportImage)
        .filter(StatusReportImage.id == image_id, StatusReportImage.status_report_id == report_id)
        .first()
    )
    if image is None:
        raise NotFoundError("Report photo")
    path = resolve_path(image.storage_key)
    return FileResponse(path, filename=image.original_filename)
