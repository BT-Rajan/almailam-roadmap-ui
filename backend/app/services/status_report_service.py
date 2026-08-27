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
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationAppError
from app.models.project import Project
from app.models.status_report import StatusReport
from app.models.task import Task
from app.models.user import User
from app.services import company_service, notification_service, task_service, timeline_service
from app.services.number_series_service import next_number

ENTITY_TYPE = "STATUS_REPORT"

# Deliberately hardcoded, not read from CompanySettings.timezone -- that
# setting is a general display preference (invoices, dashboards, and
# defaults to "Asia/Dubai" today) that an admin can change at any time
# for unrelated reasons. The daily report cutoff is a specific, stated
# business rule ("editable until 11:59 PM Kuwait time, wherever the
# engineer physically is"), not a display preference -- it must not
# silently shift if someone later changes the company's display
# timezone. Kuwait is UTC+3; Dubai is UTC+4, so conflating the two
# would move the real cutoff by an hour.
REPORT_FILING_TIMEZONE = "Asia/Kuwait"

# A cancelled project is finished -- no more field activity is expected
# on it, so no new/edited reports either, independent of what
# start_date/target_date happen to say.
_CLOSED_PROJECT_STATUSES = ("Cancelled",)


def _today(db: Session) -> date:
    """"Today" for report-filing purposes is always Kuwait local time,
    never the server's system clock or the engineer's device clock.
    Matters specifically because this app's servers commonly run on
    UTC: an engineer filing a report between roughly midnight and 3am
    Kuwait time is still the *previous* calendar day in UTC, so
    date.today() there would silently treat a genuinely new day's
    report as an edit to yesterday's already-filed one -- exactly the
    "only today's report is editable, until 11:59 PM Kuwait time"
    rule failing in the one window it actually matters. The `db`
    parameter is unused now (kept so callers don't need to change) --
    see REPORT_FILING_TIMEZONE above for why this no longer reads
    CompanySettings.timezone. Falls back to plain date.today() if
    the "Asia/Kuwait" zone can't be loaded (e.g. no tzdata installed)
    rather than raising in the middle of an unrelated action.
    """
    try:
        return datetime.now(ZoneInfo(REPORT_FILING_TIMEZONE)).date()
    except Exception:
        return date.today()


def report_filing_today(db: Session) -> date:
    """Public wrapper around _today() -- for callers outside this module
    (e.g. the API layer, computing per-project filing-window state)
    that need "today" by the same clock this module uses internally,
    without reaching into a private helper."""
    return _today(db)


def filing_window_block_reason(project: Project, report_date: date) -> str | None:
    """None if `report_date` is a valid day to file/edit a report for
    this project; otherwise a user-facing reason it isn't. Shared by
    the actual filing gate (file_todays_report) and by the projects
    list (so the portal can show/disable the right thing before the
    engineer even opens the form, not just reject on submit).

    The window is simply [start_date, target_date] inclusive -- since
    this is checked live against the project's *current* target_date
    rather than a value captured once, an extension (target_date
    pushed later) automatically widens the window with no extra code,
    and the same is true in reverse if it's ever pulled in. A closed
    project (Completed/Cancelled) blocks filing outright, even for a
    date that would otherwise be in range -- once the project is
    actually finished there's nothing left to report on regardless of
    what the planned dates say.
    """
    if project.status in _CLOSED_PROJECT_STATUSES:
        return "This project is closed. Status reports can no longer be filed for it."
    if report_date < project.start_date:
        return "This project hasn't started yet."
    if report_date > project.target_date:
        return "This project's report filing window has closed."
    return None


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


def get_todays_report_for_project(db: Session, engineer_id: int, project_id: int) -> StatusReport | None:
    return (
        db.query(StatusReport)
        .filter(
            StatusReport.engineer_id == engineer_id,
            StatusReport.project_id == project_id,
            StatusReport.report_date == _today(db),
        )
        .first()
    )


def list_todays_reports(db: Session, engineer_id: int) -> list[StatusReport]:
    """Every report this engineer has already filed today, across all
    their projects -- one engineer assigned to several projects files a
    separate report per project each day, so "today's report" is
    genuinely plural here. Used to show, per project, whether today's
    report is already filed (and pre-fillable for editing) or still
    outstanding."""
    return (
        db.query(StatusReport)
        .filter(StatusReport.engineer_id == engineer_id, StatusReport.report_date == _today(db))
        .order_by(StatusReport.project_id.asc())
        .all()
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
    """Create-or-update-today's-row *for this project* -- "file today's
    report" is a single action regardless of whether one already exists
    for today for this particular project, not a separate create vs.
    edit decision the caller has to make. An engineer assigned to
    several projects calls this once per project per day; each call is
    scoped independently by (engineer, project, day), so filing today's
    report for Project A has no effect on Project B's. Deliberately
    blocked once the report has already been reviewed and attached (see
    attach_report) -- at that point it's become the permanent basis for
    a real project timeline entry, and silently changing it out from
    under that record would make the timeline entry describe a report
    that no longer exists in its original form."""
    project = (
        db.query(Project)
        .filter(Project.project_no == project_no, Project.deleted_at.is_(None))
        .first()
    )
    if project is None:
        raise NotFoundError("Project")

    if not notes.strip():
        raise ValidationAppError("Notes are required.")

    today = _today(db)
    block_reason = filing_window_block_reason(project, today)
    if block_reason:
        raise ValidationAppError(block_reason)

    existing = get_todays_report_for_project(db, engineer_id, project.id)
    if existing:
        if existing.status == "Attached":
            raise ValidationAppError(
                "Today's report for this project has already been reviewed and attached -- it can no longer be edited."
            )
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
        report_date=today,
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
