from datetime import date, datetime, time

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, SmallInteger, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.user import BigPK

SCHEDULED_REPORT_TYPES = ("business_summary", "financial_summary", "project_status")
SCHEDULED_REPORT_PERIODS = ("last_7_days", "last_30_days", "this_month", "last_month", "this_quarter", "this_year")
SCHEDULED_REPORT_FREQUENCIES = ("once", "daily", "weekly", "monthly")
SCHEDULED_REPORT_RUN_STATUSES = ("sent", "failed")


class ScheduledReport(Base, TimestampMixin):
    """An Administration-configured "auto email report sender" -- picks a
    report (business_summary/financial_summary/project_status), renders
    it as a PDF (see app.services.scheduled_report_pdf), and emails it to
    one or more recipients on a schedule, reusing email_service's
    existing SMTP plumbing exactly like a Quotation/Contract "Email" send
    does.

    Two scheduling shapes, both expressed on this one row rather than as
    separate tables:

      - frequency='once': fires exactly once at `send_datetime` (a
        specific date+time), then deactivates itself. start_date/
        end_date/day_of_week/day_of_month are unused.
      - frequency in (daily/weekly/monthly): fires repeatedly at
        `send_time` (a time-of-day, in CompanySettings.timezone) on each
        occurrence, from `start_date` (inclusive) through `end_date`
        (inclusive) -- end_date is nullable, meaning "runs indefinitely"
        ("infinite" end date). day_of_week (0=Monday..6=Sunday) is
        required for weekly; day_of_month (1..31, clamped to the actual
        length of a given month, e.g. 31 in February lands on the 28th/
        29th) is required for monthly.

    `next_run_at` is the one column the scheduler tick (see main.py's
    _run_scheduled_reports) actually queries against -- computed and
    stored by scheduled_report_service whenever a schedule is created,
    edited, or just fired, so each tick is a cheap indexed range scan
    ("is_active AND next_run_at <= now") instead of recomputing every
    active schedule's next occurrence on every tick. Stored as a naive
    UTC datetime (Python's own clock, not the DB server's/MySQL NOW() --
    see scheduled_report_service._to_utc_naive's own comment for why),
    consistently with how status_report_service already treats "what
    time is it right now" as something this app must pin down itself
    rather than trust the server it happens to be deployed on.
    """

    __tablename__ = "scheduled_reports"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    report_type: Mapped[str] = mapped_column(Enum(*SCHEDULED_REPORT_TYPES, name="scheduled_report_type"), nullable=False)
    # Only meaningful for report_type='project_status'.
    project_id: Mapped[int | None] = mapped_column(BigPK, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    # Only meaningful for report_type='financial_summary' -- the period is
    # a rolling window computed relative to each run's date, not a fixed
    # date range, so the same schedule keeps producing "last 30 days"
    # (etc.) fresh every time it fires rather than the same dates forever.
    period: Mapped[str | None] = mapped_column(Enum(*SCHEDULED_REPORT_PERIODS, name="scheduled_report_period"), nullable=True)

    # Email addresses, validated individually at the API layer
    # (ScheduledReportIn) -- stored as a JSON array rather than a
    # comma-joined string so the admin UI can list/edit them one at a
    # time without a parse/format round-trip.
    recipients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    message_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    frequency: Mapped[str] = mapped_column(Enum(*SCHEDULED_REPORT_FREQUENCIES, name="scheduled_report_frequency"), nullable=False)
    send_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    send_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    day_of_month: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # NULL = no end date, i.e. the schedule keeps firing indefinitely.
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Indexed -- this is the column the scheduler tick filters on (see
    # this model's own docstring). NULL means "nothing left to run"
    # (either a 'once' schedule that already fired, a recurring schedule
    # whose end_date has passed, or one an admin turned off).
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(Enum(*SCHEDULED_REPORT_RUN_STATUSES, name="scheduled_report_run_status"), nullable=True)
    last_run_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_by: Mapped[int] = mapped_column(BigPK, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
