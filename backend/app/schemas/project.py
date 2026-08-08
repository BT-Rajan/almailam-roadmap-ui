from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.project import PROJECT_PRIORITIES, PROJECT_STATUSES, WORKFLOW_STAGES


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class ProjectOut(BaseModel):
    id: str
    projectNo: str
    projectName: str
    clientId: str
    service: str
    engineer: str
    currentStage: str
    progress: int
    priority: str
    startDate: date
    targetDate: date
    status: str

    @staticmethod
    def from_model(project, engineer_name: str) -> "ProjectOut":
        return ProjectOut(
            id=project.project_no,
            projectNo=project.project_no,
            projectName=project.project_name,
            clientId=f"CLT-{project.client_id:03d}",
            service=project.service,
            engineer=engineer_name,
            currentStage=project.current_stage,
            progress=project.progress,
            priority=project.priority,
            startDate=project.start_date,
            targetDate=project.target_date,
            status=project.status,
        )


class ProjectCreate(BaseModel):
    projectName: str = Field(min_length=1, max_length=200)
    clientId: str
    service: str = Field(min_length=1, max_length=100)
    engineerId: str
    priority: str = "Medium"
    startDate: date
    targetDate: date

    _check_priority = field_validator("priority")(_enum_validator(PROJECT_PRIORITIES, "priority"))

    @field_validator("targetDate")
    @classmethod
    def target_after_start(cls, value: date, info) -> date:
        start_date = info.data.get("startDate")
        if start_date is not None and value <= start_date:
            raise ValueError("targetDate must be after startDate")
        return value


class ProjectUpdate(BaseModel):
    projectName: str | None = Field(default=None, min_length=1, max_length=200)
    service: str | None = Field(default=None, min_length=1, max_length=100)
    engineerId: str | None = None
    priority: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    targetDate: date | None = None
    status: str | None = None
    currentStage: str | None = None
    reason: str | None = None

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: str | None) -> str | None:
        if value is not None and value not in PROJECT_PRIORITIES:
            raise ValueError(f"priority must be one of {PROJECT_PRIORITIES}")
        return value

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str | None) -> str | None:
        if value is not None and value not in PROJECT_STATUSES:
            raise ValueError(f"status must be one of {PROJECT_STATUSES}")
        return value

    @field_validator("currentStage")
    @classmethod
    def check_current_stage(cls, value: str | None) -> str | None:
        if value is not None and value not in WORKFLOW_STAGES:
            raise ValueError(f"currentStage must be one of {WORKFLOW_STAGES}")
        return value


class ProjectStageUpdate(BaseModel):
    currentStage: str
    reason: str | None = None
    _check = field_validator("currentStage")(_enum_validator(WORKFLOW_STAGES, "currentStage"))


class ProjectStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    _check = field_validator("status")(_enum_validator(PROJECT_STATUSES, "status"))
