from datetime import date, datetime, timezone

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.scheduled_report import (
    SCHEDULED_REPORT_FREQUENCIES,
    SCHEDULED_REPORT_PERIODS,
    SCHEDULED_REPORT_TYPES,
)


class ScheduledReportIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    reportType: str
    # Required only for reportType='project_status' -- a project_no
    # (e.g. "PRJ-0042"), not the internal numeric id, matching how every
    # other project-scoped endpoint in this app is addressed (see
    # api/reports.py's own GET /projects/{project_no}).
    projectNo: str | None = None
    # Required only for reportType='financial_summary'.
    period: str | None = None

    # At least one recipient, each validated as a real email address --
    # EmailStr both catches typos ("bob@@x.com") before this becomes an
    # SMTP failure the scheduler silently logs hours later, and matches
    # send_email/send_document_email's own convention of trusting
    # email_validator for this rather than a hand-rolled regex. Capped
    # at 5 to match the recipient limit the frontend's EmailListInput
    # enforces (ScheduledReportDialog.vue) -- kept in sync here too so a
    # request bypassing that UI can't send to more than the app-wide
    # cap intends.
    recipients: list[EmailStr] = Field(min_length=1, max_length=5)
    subject: str | None = Field(default=None, max_length=300)
    messageBody: str | None = None

    frequency: str
    # "HH:MM" (24h), the local time-of-day in CompanySettings.timezone
    # this fires at -- required for daily/weekly/monthly, unused for
    # 'once'.
    sendTime: str | None = None
    # Required only for frequency='once' -- the exact local date+time
    # (CompanySettings.timezone) this single send fires at.
    sendDatetime: datetime | None = None
    # 0=Monday..6=Sunday -- required only for frequency='weekly'.
    dayOfWeek: int | None = Field(default=None, ge=0, le=6)
    # 1..31 -- required only for frequency='monthly'. A month shorter
    # than this is clamped to that month's actual last day (e.g. 31 in
    # February lands on the 28th/29th) rather than skipping the month
    # entirely -- see scheduled_report_service's own comment.
    dayOfMonth: int | None = Field(default=None, ge=1, le=31)
    # Recurring schedules only -- when the schedule starts being
    # eligible to fire. Defaults to today (in the service layer) when
    # omitted. Unused for frequency='once'.
    startDate: date | None = None
    # Recurring schedules only -- when the schedule stops firing.
    # Left empty ("infinite") means it never stops on its own.
    endDate: date | None = None
    isActive: bool = True

    @field_validator("reportType")
    @classmethod
    def _validate_report_type(cls, v: str) -> str:
        if v not in SCHEDULED_REPORT_TYPES:
            raise ValueError(f"reportType must be one of: {', '.join(SCHEDULED_REPORT_TYPES)}.")
        return v

    @field_validator("period")
    @classmethod
    def _validate_period(cls, v: str | None) -> str | None:
        if v is not None and v not in SCHEDULED_REPORT_PERIODS:
            raise ValueError(f"period must be one of: {', '.join(SCHEDULED_REPORT_PERIODS)}.")
        return v

    @field_validator("frequency")
    @classmethod
    def _validate_frequency(cls, v: str) -> str:
        if v not in SCHEDULED_REPORT_FREQUENCIES:
            raise ValueError(f"frequency must be one of: {', '.join(SCHEDULED_REPORT_FREQUENCIES)}.")
        return v

    @field_validator("sendTime")
    @classmethod
    def _validate_send_time(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            hours, minutes = v.split(":")
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError
        except ValueError as exc:
            raise ValueError("sendTime must be in HH:MM (24-hour) format.") from exc
        return v

    @field_validator("name", "subject", "messageBody", mode="before")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


class ScheduledReportOut(BaseModel):
    id: str
    name: str
    reportType: str
    projectNo: str | None
    period: str | None
    recipients: list[str]
    subject: str | None
    messageBody: str | None
    frequency: str
    sendTime: str | None
    sendDatetime: datetime | None
    dayOfWeek: int | None
    dayOfMonth: int | None
    startDate: date | None
    endDate: date | None
    isActive: bool
    nextRunAt: datetime | None
    lastRunAt: datetime | None
    lastRunStatus: str | None
    lastRunError: str | None
    createdBy: str
    createdAt: datetime
    updatedAt: datetime

    @staticmethod
    def from_model(row, project_no: str | None, created_by_name: str) -> "ScheduledReportOut":
        # next_run_at/last_run_at are stored as naive-but-UTC (see
        # scheduled_report_service's own comment on why) -- tagged with
        # tzinfo here so the JSON goes out with an explicit UTC offset
        # and the frontend's `new Date(...)` parses it correctly instead
        # of misreading these UTC clock numbers as browser-local time.
        # send_datetime, by contrast, is the admin's original *local*
        # (CompanySettings.timezone) input for a 'once' schedule and is
        # deliberately left naive/untagged here.
        return ScheduledReportOut(
            id=str(row.id),
            name=row.name,
            reportType=row.report_type,
            projectNo=project_no,
            period=row.period,
            recipients=row.recipients,
            subject=row.subject,
            messageBody=row.message_body,
            frequency=row.frequency,
            sendTime=row.send_time.strftime("%H:%M") if row.send_time else None,
            sendDatetime=row.send_datetime,
            dayOfWeek=row.day_of_week,
            dayOfMonth=row.day_of_month,
            startDate=row.start_date,
            endDate=row.end_date,
            isActive=row.is_active,
            nextRunAt=row.next_run_at.replace(tzinfo=timezone.utc) if row.next_run_at else None,
            lastRunAt=row.last_run_at.replace(tzinfo=timezone.utc) if row.last_run_at else None,
            lastRunStatus=row.last_run_status,
            lastRunError=row.last_run_error,
            createdBy=created_by_name,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )
