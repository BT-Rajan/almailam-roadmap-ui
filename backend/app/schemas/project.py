from datetime import date, datetime

from pydantic import BaseModel, Field, condecimal, field_validator

from app.models.project import PROJECT_PRIORITIES, PROJECT_STATUSES, WORKFLOW_STAGES


def _enum_validator(allowed: tuple[str, ...], label: str):
    def _check(value: str) -> str:
        if value not in allowed:
            raise ValueError(f"{label} must be one of {allowed}")
        return value

    return _check


class SelectedActivityOut(BaseModel):
    serviceId: str
    serviceName: str
    activityId: str
    activityName: str
    fixedCost: float

    @staticmethod
    def from_model(activity) -> "SelectedActivityOut":
        return SelectedActivityOut(
            serviceId=activity.service_id,
            serviceName=activity.service_name,
            activityId=activity.activity_id,
            activityName=activity.activity_name,
            fixedCost=float(activity.fixed_cost),
        )


class SelectedActivityIn(BaseModel):
    serviceId: str = Field(min_length=1, max_length=20)
    serviceName: str = Field(min_length=1, max_length=150)
    activityId: str = Field(min_length=1, max_length=20)
    activityName: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2)  # type: ignore[valid-type]


class ProjectOut(BaseModel):
    id: str
    projectNo: str
    projectName: str
    description: str | None = None
    clientId: str
    service: str
    engineer: str
    currentStage: str
    progress: int
    priority: str
    startDate: date
    targetDate: date
    status: str
    # Granular breakdown from the service picker, and its total -- both
    # optional/empty for projects created before this existed or without
    # any picks. This is what NewQuotationDialog/NewContractDialog read to
    # prefill line items from the services actually picked for the project.
    selectedActivities: list[SelectedActivityOut] = Field(default_factory=list)
    serviceTotal: float | None = None
    completedAt: datetime | None = None
    # Permit names the client confirmed, at project setup, they already
    # hold -- each is a mandatory upload requirement on the Documents
    # tab (see ProjectDocumentsTab.vue's permitChecklist).
    requiredPermitDocuments: list[str] = Field(default_factory=list)

    @staticmethod
    def from_model(project, engineer_name: str, selected_activities: list | None = None) -> "ProjectOut":
        return ProjectOut(
            id=project.project_no,
            projectNo=project.project_no,
            projectName=project.project_name,
            description=project.description,
            clientId=f"CLT-{project.client_id:03d}",
            service=project.service,
            engineer=engineer_name,
            currentStage=project.current_stage,
            progress=project.progress,
            priority=project.priority,
            startDate=project.start_date,
            targetDate=project.target_date,
            status=project.status,
            selectedActivities=[SelectedActivityOut.from_model(a) for a in (selected_activities or [])],
            serviceTotal=float(project.service_total) if project.service_total is not None else None,
            completedAt=project.completed_at,
            requiredPermitDocuments=list(project.required_permit_documents or []),
        )


class ScopeDeviationOut(BaseModel):
    revision: str
    date: date
    changedBy: str
    summary: str


class CompletionSummaryOut(BaseModel):
    plannedBudget: float | None
    actualBudget: float | None
    plannedDurationDays: int
    actualDurationDays: int | None
    completedAt: datetime | None
    notes: str | None
    scopeDeviations: list[ScopeDeviationOut] = Field(default_factory=list)
    deviationNotes: str | None


class CompletionNotesUpdate(BaseModel):
    notes: str = Field(default="", max_length=4000)


class DeviationNotesUpdate(BaseModel):
    notes: str = Field(default="", max_length=4000)


class ScopeChangeUpdate(BaseModel):
    description: str = Field(min_length=1, max_length=2000)
    contractUpdateNeeded: bool
    paymentUpdateNeeded: bool


class ProjectCreate(BaseModel):
    projectName: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    clientId: str
    service: str = Field(min_length=1, max_length=100)
    engineerId: str
    priority: str = "Medium"
    startDate: date
    targetDate: date
    selectedActivities: list[SelectedActivityIn] | None = None
    serviceTotal: condecimal(ge=0, max_digits=12, decimal_places=2) | None = None  # type: ignore[valid-type]
    # Permits the client confirmed they already hold -- each becomes a
    # mandatory upload requirement on the Documents tab. Permits the
    # client doesn't have yet aren't sent here at all; the wizard turns
    # those into Tasks instead, against the project this call returns.
    requiredPermitDocuments: list[str] = Field(default_factory=list)

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
    description: str | None = Field(default=None, max_length=2000)
    service: str | None = Field(default=None, min_length=1, max_length=100)
    engineerId: str | None = None
    priority: str | None = None
    # progress is deliberately not here -- it's computed from the
    # execution-step checklist (execution_step_service.py), not settable
    # directly. See ProjectOut.progress for the (read-only) computed value.
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
