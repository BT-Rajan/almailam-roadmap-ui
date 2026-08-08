from datetime import date, time

from pydantic import BaseModel, Field, field_validator

from app.models.task import TASK_PRIORITIES, TASK_SEVERITIES, TASK_STATUSES


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class TaskOut(BaseModel):
    id: str
    projectId: str
    title: str
    assignedTo: str
    priority: str
    severity: str
    dueDate: date
    dueTime: str
    status: str

    @staticmethod
    def from_model(task, project_no: str, assigned_to_name: str) -> "TaskOut":
        return TaskOut(
            id=task.task_no,
            projectId=project_no,
            title=task.title,
            assignedTo=assigned_to_name,
            priority=task.priority,
            severity=task.severity,
            dueDate=task.due_date,
            dueTime=task.due_time.strftime("%H:%M"),
            status=task.status,
        )


class TaskCreate(BaseModel):
    projectId: str
    title: str = Field(min_length=1, max_length=200)
    assignedTo: str
    priority: str = "Medium"
    severity: str = "Minor"
    dueDate: date
    dueTime: time

    _check_priority = field_validator("priority")(_enum_validator(TASK_PRIORITIES, "priority"))
    _check_severity = field_validator("severity")(_enum_validator(TASK_SEVERITIES, "severity"))


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    assignedTo: str | None = None
    priority: str | None = None
    severity: str | None = None
    dueDate: date | None = None
    dueTime: time | None = None
    status: str | None = None
    reason: str | None = None

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: str | None) -> str | None:
        if value is not None and value not in TASK_PRIORITIES:
            raise ValueError(f"priority must be one of {TASK_PRIORITIES}")
        return value

    @field_validator("severity")
    @classmethod
    def check_severity(cls, value: str | None) -> str | None:
        if value is not None and value not in TASK_SEVERITIES:
            raise ValueError(f"severity must be one of {TASK_SEVERITIES}")
        return value

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in TASK_STATUSES:
            raise ValueError(f"status must be one of {TASK_STATUSES}")
        return value


class TaskStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(TASK_STATUSES, "status"))
