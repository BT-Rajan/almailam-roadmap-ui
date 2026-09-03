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


class SelectedSupervisionActivityOut(BaseModel):
    activityId: str
    activityName: str
    monthlyRate: float
    startDate: date
    endDate: date | None = None

    @staticmethod
    def from_model(activity) -> "SelectedSupervisionActivityOut":
        return SelectedSupervisionActivityOut(
            activityId=activity.activity_id,
            activityName=activity.activity_name,
            monthlyRate=float(activity.monthly_rate),
            startDate=activity.start_date,
            endDate=activity.end_date,
        )


class SelectedSupervisionActivityIn(BaseModel):
    activityId: str = Field(min_length=1, max_length=20)
    activityName: str = Field(min_length=1, max_length=150)
    monthlyRate: condecimal(ge=0, max_digits=12, decimal_places=2)  # type: ignore[valid-type]
    startDate: date
    endDate: date | None = None

    @field_validator("endDate")
    @classmethod
    def end_after_start(cls, value: date | None, info) -> date | None:
        start_date = info.data.get("startDate")
        if value is not None and start_date is not None and value < start_date:
            raise ValueError("endDate must not be before startDate")
        return value


class ProjectOut(BaseModel):
    id: str
    projectNo: str
    projectName: str
    description: str | None = None
    # Internal approval of `description` (the scope-of-work text) at the
    # Requirement stage -- see ScopeOfWorkOut for the full revision
    # history behind it.
    scopeStatus: str
    scopeApprovedAt: datetime | None = None
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
    # The Supervision activities picked at project setup, and their
    # combined nominal monthly total -- same "optional, empty for older
    # projects" reasoning as selectedActivities/serviceTotal above.
    # supervisionStartDate/supervisionEndDate are the overall Supervision
    # engagement window, captured separately from each activity's own
    # startDate/endDate (see ProjectSelectedSupervisionActivity's model
    # docstring). The real, day-prorated billing schedule lives on the
    # Supervision financial agreement once one is created, not here.
    selectedSupervisionActivities: list[SelectedSupervisionActivityOut] = Field(default_factory=list)
    supervisionMonthlyTotal: float | None = None
    supervisionStartDate: date | None = None
    supervisionEndDate: date | None = None
    # Whether this project's workflow includes a Design and/or
    # Supervision stage -- see project_service.compute_stage_flags for
    # how these are derived. Drives which of the Design/Supervision
    # stepper nodes and workspace tabs are shown on the frontend.
    includesDesign: bool = False
    includesSupervision: bool = False
    # Permit names the client confirmed, at project setup, they already
    # hold -- each is a mandatory upload requirement on the Documents
    # tab (see ProjectDocumentsTab.vue's permitChecklist).
    requiredPermitDocuments: list[str] = Field(default_factory=list)
    # The project/plot address (migration 0063) -- fills a Quotation/
    # Contract document template's address placeholder. Distinct from
    # any of the client's own ClientAddress rows.
    siteAddress: str | None = None

    @staticmethod
    def from_model(
        project, engineer_name: str, selected_activities: list | None = None,
        selected_supervision_activities: list | None = None,
        includes_design: bool = False, includes_supervision: bool = False,
    ) -> "ProjectOut":
        return ProjectOut(
            id=project.project_no,
            projectNo=project.project_no,
            projectName=project.project_name,
            description=project.description,
            scopeStatus=project.scope_status,
            scopeApprovedAt=project.scope_approved_at,
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
            selectedSupervisionActivities=[
                SelectedSupervisionActivityOut.from_model(a) for a in (selected_supervision_activities or [])
            ],
            supervisionMonthlyTotal=(
                float(project.supervision_monthly_total) if project.supervision_monthly_total is not None else None
            ),
            supervisionStartDate=project.supervision_start_date,
            supervisionEndDate=project.supervision_end_date,
            includesDesign=includes_design,
            includesSupervision=includes_supervision,
            requiredPermitDocuments=list(project.required_permit_documents or []),
            siteAddress=project.site_address,
        )


class ScopeRevisionOut(BaseModel):
    id: str
    revision: str
    date: date
    changedBy: str
    summary: str
    hasDocument: bool
    documentName: str | None = None

    @staticmethod
    def from_model(revision, changed_by_name: str) -> "ScopeRevisionOut":
        return ScopeRevisionOut(
            id=f"PSR-{revision.id:03d}",
            revision=revision.revision,
            date=revision.revised_at,
            changedBy=changed_by_name,
            summary=revision.summary,
            hasDocument=bool(revision.storage_key),
            documentName=revision.original_filename,
        )


class ScopeOfWorkOut(BaseModel):
    description: str | None
    scopeStatus: str
    scopeApprovedAt: datetime | None
    scopeApprovedBy: str | None
    revisions: list[ScopeRevisionOut] = Field(default_factory=list)


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
    # The Supervision activities picked in the New Project wizard's
    # unified service picker. None/absent for callers that pick no
    # Supervision work at all (it's optional -- not every engagement
    # needs it). supervisionStartDate/supervisionEndDate are the overall
    # engagement window, separate from each activity's own dates --
    # create_project() requires supervisionStartDate whenever any
    # activities are selected.
    selectedSupervisionActivities: list[SelectedSupervisionActivityIn] | None = None
    supervisionStartDate: date | None = None
    supervisionEndDate: date | None = None
    # Permits the client confirmed they already hold -- each becomes a
    # mandatory upload requirement on the Documents tab. Permits the
    # client doesn't have yet aren't sent here at all; the wizard turns
    # those into Tasks instead, against the project this call returns.
    requiredPermitDocuments: list[str] = Field(default_factory=list)
    siteAddress: str | None = Field(default=None, max_length=300)

    _check_priority = field_validator("priority")(_enum_validator(PROJECT_PRIORITIES, "priority"))

    @field_validator("targetDate")
    @classmethod
    def target_after_start(cls, value: date, info) -> date:
        start_date = info.data.get("startDate")
        if start_date is not None and value <= start_date:
            raise ValueError("targetDate must be after startDate")
        return value

    @field_validator("supervisionEndDate")
    @classmethod
    def supervision_end_after_start(cls, value: date | None, info) -> date | None:
        start_date = info.data.get("supervisionStartDate")
        if value is not None and start_date is not None and value < start_date:
            raise ValueError("supervisionEndDate must not be before supervisionStartDate")
        return value


class ProjectUpdate(BaseModel):
    projectName: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    siteAddress: str | None = Field(default=None, max_length=300)
    service: str | None = Field(default=None, min_length=1, max_length=100)
    engineerId: str | None = None
    priority: str | None = None
    # progress is deliberately not here -- it's computed from
    # current_stage (project_service.recompute_progress), not settable
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


class AddServicesInput(BaseModel):
    """Adds more billable Design and/or Supervision activities to an
    existing project at any point in its lifecycle -- see
    project_service.add_selected_services. Only genuinely new activities
    (by activityId) are inserted; anything already selected is silently
    left alone rather than duplicated or re-validated."""

    designActivities: list[SelectedActivityIn] = []
    supervisionActivities: list[SelectedSupervisionActivityIn] = []
    # Only required the first time Supervision activities are added to a
    # project that has never had a Supervision window before -- mirrors
    # ProjectCreate's own supervisionStartDate/supervisionEndDate fields
    # exactly (see create_project). Ignored once the project already has
    # a window: each new activity's own dates are validated against that
    # existing window instead, same as _persist_supervision_selection
    # already does for every other Supervision activity.
    supervisionStartDate: date | None = None
    supervisionEndDate: date | None = None


class StageEligibilityOut(BaseModel):
    """One entry per structurally-reachable next stage for this project
    right now -- see project_service.get_stage_eligibility. A stage the
    project can't reach at all (e.g. Design when it has no Design work)
    is left out entirely rather than reported ineligible."""

    stage: str
    eligible: bool
    reason: str | None = None


