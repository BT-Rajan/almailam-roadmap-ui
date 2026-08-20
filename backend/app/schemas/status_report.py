from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.status_report import STATUS_REPORT_SUPERVISION_TYPES


def _enum_validator(allowed: tuple, field_name: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{field_name} must be one of {allowed}")
        return value

    return _check


class StatusReportFileRequest(BaseModel):
    """Used for both filing and editing today's report -- see
    status_report_service.file_todays_report, a single upsert rather
    than separate create/update calls."""

    projectId: str
    receiptType: str | None = Field(default=None, max_length=200)
    supervisionType: str = "Full-time"
    notes: str = Field(min_length=1, max_length=5000)
    _check = field_validator("supervisionType")(_enum_validator(STATUS_REPORT_SUPERVISION_TYPES, "supervisionType"))


class StatusReportOut(BaseModel):
    id: str
    reportNo: str
    projectId: str
    projectName: str
    engineerId: str
    engineerName: str
    reportDate: date
    receiptType: str | None
    supervisionType: str
    notes: str
    status: str
    attachedTaskId: str | None = None
    attachedBy: str | None = None
    attachedAt: datetime | None = None
    createdAt: datetime

    @staticmethod
    def from_model(report, project_no: str, project_name: str, engineer_name: str, attached_by_name: str | None, attached_task_no: str | None) -> "StatusReportOut":
        return StatusReportOut(
            id=str(report.id),
            reportNo=report.report_no,
            projectId=project_no,
            projectName=project_name,
            engineerId=f"USR-{report.engineer_id:03d}",
            engineerName=engineer_name,
            reportDate=report.report_date,
            receiptType=report.receipt_type,
            supervisionType=report.supervision_type,
            notes=report.notes,
            status=report.status,
            attachedTaskId=attached_task_no,
            attachedBy=attached_by_name,
            attachedAt=report.attached_at,
            createdAt=report.created_at,
        )


class StatusReportAttachRequest(BaseModel):
    taskId: str | None = None
    notes: str = Field(min_length=1, max_length=2000)


class EngineerProjectOption(BaseModel):
    id: str
    projectName: str
