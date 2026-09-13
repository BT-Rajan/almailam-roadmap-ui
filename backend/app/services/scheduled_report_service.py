"""Administration > Scheduled Reports -- CRUD for ScheduledReport rows,
next_run_at scheduling math, and the actual "render + email" run step
that main.py's scheduler tick (_run_scheduled_reports) calls.

Scheduling design, in one place since it's the part that isn't obvious
from the model alone:

  - `next_run_at` is the single source of truth for "when does this
    fire next" -- computed here (compute_next_run) and persisted
    whenever a schedule is created, edited, or fires, so the scheduler
    tick itself never has to recompute anything; it just asks the
    database for every active row whose next_run_at has arrived.
  - Recurring schedules (daily/weekly/monthly) are evaluated in
    CompanySettings.timezone as a wall-clock time-of-day, then converted
    to a naive UTC datetime for storage/comparison -- see
    _to_utc_naive's own comment for why naive-UTC (not the DB server's
    clock, not a tz-aware column) was chosen.
  - Firing order for run_due_schedules/_fire is deliberately
    "compute+persist the next occurrence, THEN render and send": if the
    process crashes or the send fails partway through, the schedule has
    already moved past this occurrence rather than being retried
    indefinitely on every subsequent tick (a broken recipient address
    would otherwise retry-storm the mail server every 5 minutes
    forever). The failure is still recorded (last_run_status/
    last_run_error) so an admin looking at the list can see it needs
    attention -- it just isn't auto-retried.
"""

import calendar
import logging
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.project import Project
from app.models.scheduled_report import ScheduledReport
from app.models.user import User
from app.schemas.scheduled_report import ScheduledReportIn
from app.services import audit_service, company_service, email_service, scheduled_report_pdf

logger = logging.getLogger("app.scheduled_reports")

ENTITY_TYPE = "SCHEDULED_REPORT"
_FALLBACK_TIMEZONE = "Asia/Dubai"


# ---------------------------------------------------------------------------
# Timezone / next-run-at math
# ---------------------------------------------------------------------------

def _company_tz(db: Session) -> ZoneInfo:
    tz_name = company_service.get_settings(db).timezone or _FALLBACK_TIMEZONE
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo(_FALLBACK_TIMEZONE)


def _to_utc_naive(local_dt: datetime, tz: ZoneInfo) -> datetime:
    """A wall-clock datetime, understood as being in `tz`, converted to a
    plain (tzinfo-stripped) UTC datetime for storage. Naive-but-UTC
    rather than a tz-aware column: this app's DateTime columns are
    naive throughout (see models/mixins.py's TimestampMixin -- MySQL's
    DATETIME has no offset), and comparing against Python's own
    datetime.now(timezone.utc) (not the DB server's NOW(), which this
    app already treats as untrustworthy -- see status_report_service's
    REPORT_FILING_TIMEZONE comment) is what keeps the scheduler tick's
    "is this due yet" check correct regardless of what timezone the
    server itself happens to be configured in."""
    return local_dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)


def _month_day_clamped(year: int, month: int, day_of_month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day_of_month, last_day))


def _first_local_date_on_or_after(schedule: ScheduledReport, min_date: date) -> date:
    """The earliest calendar date >= min_date this schedule's frequency
    could fire on, ignoring end_date (checked by the caller)."""
    if schedule.frequency == "daily":
        return min_date
    if schedule.frequency == "weekly":
        delta = (schedule.day_of_week - min_date.weekday()) % 7
        return min_date + timedelta(days=delta)
    if schedule.frequency == "monthly":
        candidate = _month_day_clamped(min_date.year, min_date.month, schedule.day_of_month)
        if candidate >= min_date:
            return candidate
        year, month = (min_date.year + 1, 1) if min_date.month == 12 else (min_date.year, min_date.month + 1)
        return _month_day_clamped(year, month, schedule.day_of_month)
    raise ValidationAppError(f"Unknown frequency: {schedule.frequency}.")


def compute_next_run(schedule: ScheduledReport, tz: ZoneInfo, after: datetime | None = None) -> datetime | None:
    """The next UTC instant this schedule should fire at, or None if it
    has nothing left to run.

    `after` is the naive-UTC instant of the occurrence that was *just*
    fired (omit it when computing a schedule's very first run, e.g. on
    create/edit) -- the next occurrence must land strictly after it, so
    a schedule can never immediately re-fire for the same slot."""
    if schedule.frequency == "once":
        if after is not None:
            return None  # already fired -- a 'once' schedule never runs again
        return _to_utc_naive(schedule.send_datetime, tz) if schedule.send_datetime else None

    now_local = datetime.now(tz)
    if after is not None:
        after_local_date = after.replace(tzinfo=timezone.utc).astimezone(tz).date()
        min_date = after_local_date + timedelta(days=1)
    else:
        min_date = schedule.start_date or now_local.date()
        min_date = max(min_date, now_local.date())

    candidate_date = _first_local_date_on_or_after(schedule, min_date)
    candidate_dt = datetime.combine(candidate_date, schedule.send_time)
    # On a fresh (not "after a run") computation, today's slot may have
    # already passed this instant -- e.g. creating a 9:00 AM daily
    # schedule at 2:00 PM should start tomorrow, not immediately.
    if after is None and candidate_dt <= now_local.replace(tzinfo=None):
        candidate_date = _first_local_date_on_or_after(schedule, min_date + timedelta(days=1))
        candidate_dt = datetime.combine(candidate_date, schedule.send_time)

    if schedule.end_date is not None and candidate_dt.date() > schedule.end_date:
        return None
    return _to_utc_naive(candidate_dt, tz)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def list_schedules(db: Session) -> list[ScheduledReport]:
    return db.query(ScheduledReport).order_by(ScheduledReport.created_at.desc()).all()


def get_schedule(db: Session, schedule_id: int) -> ScheduledReport:
    schedule = db.query(ScheduledReport).filter(ScheduledReport.id == schedule_id).first()
    if schedule is None:
        raise NotFoundError("Scheduled report")
    return schedule


def project_no_for(db: Session, schedule: ScheduledReport) -> str | None:
    if schedule.project_id is None:
        return None
    project = db.query(Project).filter(Project.id == schedule.project_id).first()
    return project.project_no if project else None


def creator_name(db: Session, schedule: ScheduledReport) -> str:
    user = db.query(User).filter(User.id == schedule.created_by).first()
    return user.full_name if user else "Unknown"


def _resolve_project_id(db: Session, project_no: str | None) -> int | None:
    if project_no is None:
        return None
    project = db.query(Project).filter(Project.project_no == project_no, Project.deleted_at.is_(None)).first()
    if project is None:
        raise ValidationAppError(f"Project '{project_no}' was not found.")
    return project.id


def _parse_send_time(value: str | None) -> time | None:
    if value is None:
        return None
    hours, minutes = value.split(":")
    return time(hour=int(hours), minute=int(minutes))


def _validate_schedule_fields(payload: ScheduledReportIn, tz: ZoneInfo) -> None:
    if payload.reportType == "project_status" and not payload.projectNo:
        raise ValidationAppError("Select a project for a project status report.")

    if payload.frequency == "once":
        if payload.sendDatetime is None:
            raise ValidationAppError("Pick the date and time this report should be sent.")
        if payload.isActive and payload.sendDatetime <= datetime.now(tz).replace(tzinfo=None):
            raise ValidationAppError("The send date and time must be in the future.")
        return

    # daily / weekly / monthly
    if payload.sendTime is None:
        raise ValidationAppError("Pick the time of day this report should be sent.")
    if payload.frequency == "weekly" and payload.dayOfWeek is None:
        raise ValidationAppError("Pick which day of the week this report should be sent.")
    if payload.frequency == "monthly" and payload.dayOfMonth is None:
        raise ValidationAppError("Pick which day of the month this report should be sent.")
    if payload.endDate is not None:
        start = payload.startDate or date.today()
        if payload.endDate < start:
            raise ValidationAppError("The end date can't be before the start date.")


def _apply_payload(schedule: ScheduledReport, payload: ScheduledReportIn, project_id: int | None) -> None:
    schedule.name = payload.name
    schedule.report_type = payload.reportType
    schedule.project_id = project_id
    schedule.period = payload.period
    schedule.recipients = [str(r) for r in payload.recipients]
    schedule.subject = payload.subject
    schedule.message_body = payload.messageBody
    schedule.frequency = payload.frequency
    schedule.send_time = _parse_send_time(payload.sendTime)
    schedule.send_datetime = payload.sendDatetime
    schedule.day_of_week = payload.dayOfWeek
    schedule.day_of_month = payload.dayOfMonth
    schedule.start_date = payload.startDate or (date.today() if payload.frequency != "once" else None)
    schedule.end_date = payload.endDate
    schedule.is_active = payload.isActive


def create_schedule(db: Session, payload: ScheduledReportIn, actor_id: int) -> ScheduledReport:
    tz = _company_tz(db)
    _validate_schedule_fields(payload, tz)
    project_id = _resolve_project_id(db, payload.projectNo)

    schedule = ScheduledReport(created_by=actor_id)
    _apply_payload(schedule, payload, project_id)
    schedule.next_run_at = compute_next_run(schedule, tz) if schedule.is_active else None

    db.add(schedule)
    db.flush()
    audit_service.log_event(db, ENTITY_TYPE, schedule.id, f"Scheduled report '{schedule.name}' created", actor_id)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, schedule_id: int, payload: ScheduledReportIn, actor_id: int) -> ScheduledReport:
    schedule = get_schedule(db, schedule_id)
    tz = _company_tz(db)
    _validate_schedule_fields(payload, tz)
    project_id = _resolve_project_id(db, payload.projectNo)

    _apply_payload(schedule, payload, project_id)
    # Recomputed from scratch on every edit (not incrementally) -- any
    # field that affects timing (frequency, send time/date, start/end
    # date) may have just changed, so the only correct next_run_at is a
    # fresh one, same as if the schedule were being created now.
    schedule.next_run_at = compute_next_run(schedule, tz) if schedule.is_active else None

    audit_service.log_event(db, ENTITY_TYPE, schedule.id, f"Scheduled report '{schedule.name}' updated", actor_id)
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule_id: int, actor_id: int) -> None:
    schedule = get_schedule(db, schedule_id)
    audit_service.log_event(db, ENTITY_TYPE, schedule.id, f"Scheduled report '{schedule.name}' deleted", actor_id)
    db.delete(schedule)
    db.commit()


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------

_DEFAULT_BODY = (
    "Please find attached the {title}, generated automatically.\n\n"
    "This is an automated message from ServiceOS \u2014 no reply is needed."
)


def _send(db: Session, schedule: ScheduledReport, run_at: datetime) -> None:
    pdf_bytes, filename, title = scheduled_report_pdf.render(db, schedule, run_at)
    subject = schedule.subject or title
    body = (schedule.message_body or _DEFAULT_BODY).format(title=title)
    # One send, every recipient in the To header (RFC 5322 allows a
    # comma-separated address list there) -- simpler than N separate
    # sends, and this is an internal distribution list an admin
    # configured themselves, not a customer-facing broadcast where
    # recipients seeing each other would be a privacy problem.
    email_service.send_document_email(
        to_email=", ".join(schedule.recipients),
        subject=subject,
        body_text=body,
        attachment_bytes=pdf_bytes,
        attachment_filename=filename,
        attachment_mimetype="application/pdf",
        db=db,
    )


def send_test_now(db: Session, schedule_id: int) -> None:
    """Administration's "Send Test Now" action -- renders and sends
    immediately using the schedule's current (possibly unsaved-if-called-
    mid-edit -- callers always save first) configuration, without
    touching next_run_at/last_run_* at all, so it can never interfere
    with the schedule's real, unattended run."""
    schedule = get_schedule(db, schedule_id)
    _send(db, schedule, datetime.now(timezone.utc))


def _fire(db: Session, schedule: ScheduledReport, now_utc: datetime, tz: ZoneInfo) -> None:
    fired_at = schedule.next_run_at
    # Advance (and persist) next_run_at BEFORE attempting the send -- see
    # this module's docstring for why: a failure below must not leave
    # this schedule permanently "due" and retried every tick.
    schedule.next_run_at = compute_next_run(schedule, tz, after=fired_at)
    if schedule.frequency == "once":
        schedule.is_active = False
    schedule.last_run_at = now_utc
    db.commit()

    try:
        _send(db, schedule, now_utc)
    except Exception as exc:
        logger.exception("Scheduled report %s ('%s') failed to send.", schedule.id, schedule.name)
        schedule.last_run_status = "failed"
        schedule.last_run_error = str(exc)[:500]
    else:
        schedule.last_run_status = "sent"
        schedule.last_run_error = None
    db.commit()


def run_due_schedules(db: Session) -> int:
    """Called by main.py's scheduler tick. Coarse polling interval
    (see main.py's own comment on the job) plus this being a single
    cheap indexed query is the whole reason this doesn't add meaningful
    load: on a tick with nothing due (the overwhelmingly common case),
    this is one SELECT that returns zero rows."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    due = (
        db.query(ScheduledReport)
        .filter(ScheduledReport.is_active.is_(True))
        .filter(ScheduledReport.next_run_at.isnot(None))
        .filter(ScheduledReport.next_run_at <= now_utc)
        .all()
    )
    if not due:
        return 0

    tz = _company_tz(db)
    sent = 0
    for schedule in due:
        try:
            _fire(db, schedule, now_utc, tz)
            sent += 1
        except Exception:
            # _fire already commits its own failure state around the
            # send itself; this guards the surrounding bookkeeping (e.g.
            # compute_next_run raising on bad data) so one broken
            # schedule can't stop the rest of the batch from running.
            logger.exception("Failed to process scheduled report %s.", schedule.id)
            db.rollback()
    return sent
