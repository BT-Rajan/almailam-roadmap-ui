"""Site Engineer Portal's status reports -- digitizes the paper
"تقرير إشراف" (Supervision Report) form. Two sides:

  - The filing engineer: list their own projects, file/edit *today's*
    report, view their own report history (list_reports_for_engineer,
    used for the portal's read-only calendar).
  - The designated recipient (CompanySettings.status_report_recipient_id):
    review incoming reports (list_inbox) and attach one to the relevant
    project as a real timeline entry (attach_report) -- project, task,
    reporter name, and date/time all come from the report itself; only
    the recipient's own notes are freshly typed.
"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationAppError
from app.models.project import Project
from app.models.status_report import StatusReport
from app.models.task import Task
from app.models.user import User
from app.services import company_service, notification_service, task_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "STATUS_REPORT"


def list_engineer_projects(db: Session, engineer_id: int) -> list[Project]:
    """Projects to offer in the report-filing project picker -- the ones
    this engineer is actually assigned to, not every project in the
    system. Deliberately not status-filtered (an engineer might
    legitimately still be filing a report against a project mid-
    handover even if its status just changed) -- this is a picker
    convenience, not a business-rule gate."""
    return (
        db.query(Project)
        .filter(Project.engineer_id == engineer_id, Project.deleted_at.is_(None))
        .order_by(Project.project_name.asc())
        .all()
    )


def _assert_owns_report(report: StatusReport, engineer_id: int) -> None:
    if report.engineer_id != engineer_id:
        raise PermissionDeniedError()


def get_own_report(db: Session, report_id: int, engineer_id: int) -> StatusReport:
    report = db.query(StatusReport).filter(StatusReport.id == report_id).first()
    if report is None:
        raise NotFoundError("Status report")
    _assert_owns_report(report, engineer_id)
    return report


def get_todays_report(db: Session, engineer_id: int) -> StatusReport | None:
    return (
        db.query(StatusReport)
        .filter(StatusReport.engineer_id == engineer_id, StatusReport.report_date == date.today())
        .first()
    )


def list_reports_for_engineer(db: Session, engineer_id: int, start: date, end: date) -> list[StatusReport]:
    """Backs the portal's read-only calendar -- start/end define the
    visible month (or whatever range the frontend requests)."""
    return (
        db.query(StatusReport)
        .filter(
            StatusReport.engineer_id == engineer_id,
            StatusReport.report_date >= start,
            StatusReport.report_date <= end,
        )
        .order_by(StatusReport.report_date.desc())
        .all()
    )


def file_todays_report(
    db: Session,
    engineer_id: int,
    project_no: str,
    receipt_type: str | None,
    supervision_type: str,
    notes: str,
) -> StatusReport:
    """Create-or-update-today's-row -- "file today's report" is a single
    action regardless of whether one already exists for today, not a
    separate create vs. edit decision the caller has to make.
    Deliberately blocked once the report has already been reviewed and
    attached (see attach_report) -- at that point it's become the
    permanent basis for a real project timeline entry, and silently
    changing it out from under that record would make the timeline
    entry describe a report that no longer exists in its original
    form."""
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.is_(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Project")

    if not notes.strip():
        raise ValidationAppError("Notes are required.")

    existing = get_todays_report(db, engineer_id)
    if existing:
        if existing.status == "Attached":
            raise ValidationAppError(
                "Today's report has already been reviewed and attached to the project -- it can no longer be edited."
            )
        existing.project_id = project.id
        existing.receipt_type = receipt_type
        existing.supervision_type = supervision_type
        existing.notes = notes
        db.commit()
        db.refresh(existing)
        return existing

    report = StatusReport(
        report_no=next_number(db, "STATUS_REPORT"),
        project_id=project.id,
        engineer_id=engineer_id,
        report_date=date.today(),
        receipt_type=receipt_type,
        supervision_type=supervision_type,
        notes=notes,
        status="Pending",
    )
    db.add(report)
    db.flush()

    # "the designated person will receive it" -- a passive inbox nobody
    # gets told to check isn't really receiving anything. Only fires for
    # a genuinely new report, not every edit to today's -- editing an
    # already-pending report doesn't need a second notification for the
    # same thing.
    settings = company_service.get_settings(db)
    if settings.status_report_recipient_id:
        engineer = db.query(User).filter(User.id == engineer_id).first()
        notification_service.create_notification(
            db, settings.status_report_recipient_id,
            "New status report received",
            f"{engineer.full_name if engineer else 'A site engineer'} filed a status report for {project.project_name}.",
            "System",
            link_route_name="status-reports-inbox",
        )

    db.commit()
    db.refresh(report)
    return report


def list_inbox(db: Session) -> list[StatusReport]:
    """Every report not yet reviewed, oldest first -- the recipient's
    queue, not scoped to any one project since a single recipient
    handles reports across whichever projects come in."""
    return (
        db.query(StatusReport)
        .filter(StatusReport.status == "Pending")
        .order_by(StatusReport.report_date.asc(), StatusReport.id.asc())
        .all()
    )


def get_report(db: Session, report_id: int) -> StatusReport:
    report = db.query(StatusReport).filter(StatusReport.id == report_id).first()
    if report is None:
        raise NotFoundError("Status report")
    return report


def attach_report(db: Session, report_id: int, task_no: str | None, recipient_notes: str, actor_id: int) -> StatusReport:
    """Turns a filed report into a real project timeline entry. Project,
    task (if given), reporter name, and report date/time are all pulled
    from the report itself -- recipient_notes is the only thing typed
    fresh here."""
    report = get_report(db, report_id)
    if report.status == "Attached":
        raise ValidationAppError("This report has already been attached.")
    if not recipient_notes.strip():
        raise ValidationAppError("Notes are required to attach a report.")

    task: Task | None = None
    if task_no:
        task = task_service.get_task(db, task_no)
        if task.project_id != report.project_id:
            raise ValidationAppError("The selected task does not belong to this report's project.")

    engineer = db.query(User).filter(User.id == report.engineer_id).first()
    engineer_name = engineer.full_name if engineer else "Unknown"

    description_parts = [
        f"Field report by {engineer_name} on {report.report_date.isoformat()}.",
    ]
    if report.receipt_type:
        description_parts.append(f"Receipt/Handover: {report.receipt_type}")
    description_parts.append(f"Supervision: {report.supervision_type}")
    if task:
        description_parts.append(f"Task: {task.task_no} — {task.title}")
    description_parts.append(f"Report notes: {report.notes}")
    description_parts.append(f"Reviewer notes: {recipient_notes.strip()}")

    event = timeline_service.create_system_event(
        db,
        report.project_id,
        "field_activity",
        f"Field activity reported by {engineer_name}",
        "\n\n".join(description_parts),
        actor_id,
    )
    db.flush()

    report.status = "Attached"
    report.attached_task_id = task.id if task else None
    report.attached_timeline_event_id = event.id
    report.attached_by = actor_id
    report.attached_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report
