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
    # This project's own row id (not the catalog activity_id below,
    # which stays a display-only snapshot) -- the stable identifier
    # Task.selectedActivityId and the close/reopen endpoints operate on
    # (migration 0073). Plain str(row.id), same convention used for
    # other rows with no synthetic business number (e.g. document
    # versions -- see DocumentVersionOut).
    id: str
    serviceId: str
    serviceName: str
    activityId: str
    activityName: str
    fixedCost: float
    status: str
    closedAt: datetime | None = None

    @staticmethod
    def from_model(activity) -> "SelectedActivityOut":
        return SelectedActivityOut(
            id=str(activity.id),
            serviceId=activity.service_id,
            serviceName=activity.service_name,
            activityId=activity.activity_id,
            activityName=activity.activity_name,
            fixedCost=float(activity.fixed_cost),
            status=activity.status,
            closedAt=activity.closed_at,
        )


class SelectedActivityIn(BaseModel):
    serviceId: str = Field(min_length=1, max_length=20)
    serviceName: str = Field(min_length=1, max_length=150)
    activityId: str = Field(min_length=1, max_length=20)
    activityName: str = Field(min_length=1, max_length=150)
    fixedCost: condecimal(ge=0, max_digits=12, decimal_places=2)  # type: ignore[valid-type]


class SelectedSupervisionActivityOut(BaseModel):
    # This project's own row id -- what set_supervision_status operates
    # on (migration 0074), same convention as SelectedActivityOut.id/
    # SelectedPermitOut.id.
    id: str
    activityId: str
    activityName: str
    monthlyRate: float
    startDate: date
    endDate: date | None = None
    status: str
    eligibilityMetAt: datetime | None = None
    closedAt: datetime | None = None

    @staticmethod
    def from_model(activity) -> "SelectedSupervisionActivityOut":
        return SelectedSupervisionActivityOut(
            id=str(activity.id),
            activityId=activity.activity_id,
            activityName=activity.activity_name,
            monthlyRate=float(activity.monthly_rate),
            startDate=activity.start_date,
            endDate=activity.end_date,
            status=activity.status,
            eligibilityMetAt=activity.eligibility_met_at,
            closedAt=activity.closed_at,
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


class SelectedPermitOut(BaseModel):
    """A Permit picked for a project at setup (migration 0073) -- the
    missing counterpart to SelectedActivityOut/
    SelectedSupervisionActivityOut that Permits never had before (see
    ProjectSelectedPermit). id is this row's own identity, same
    convention as SelectedActivityOut.id."""

    id: str
    # The catalog's own display id -- None if the catalog item was
    # later removed (permit_catalog_item_id is ON DELETE SET NULL);
    # permitName still shows what was originally picked either way.
    permitId: str | None = None
    permitName: str
    status: str
    eligibilityMetAt: datetime | None = None
    closedAt: datetime | None = None

    @staticmethod
    def from_model(permit) -> "SelectedPermitOut":
        return SelectedPermitOut(
            id=str(permit.id),
            permitId=f"PER-{permit.permit_catalog_item_id:03d}" if permit.permit_catalog_item_id else None,
            permitName=permit.permit_name,
            status=permit.status,
            eligibilityMetAt=permit.eligibility_met_at,
            closedAt=permit.closed_at,
        )


class SelectedPermitIn(BaseModel):
    permitId: str = Field(min_length=1, max_length=20)
    permitName: str = Field(min_length=1, max_length=150)


class ProjectOut(BaseModel):
    id: str
    projectNo: str
    projectName: str
    description: str | None = None
    # Set once the client has confirmed `description` (the scope-of-work
    # text) via email OTP -- see ScopeOfWorkOut for the full revision
    # history behind it. The sole sign-off gating the move out of the
    # Requirement stage (migration 0079 dropped the earlier staff-only
    # internal-approval step).
    scopeClientConfirmedAt: datetime | None = None
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
    # Permits picked at project setup, each with its own eligibility/
    # closure lifecycle (migration 0073) -- see ProjectSelectedPermit.
    # The Permit track becomes "ready" per-item (see
    # project_service._recompute_permit_eligibility), independent of
    # Design/Supervision.
    selectedPermits: list[SelectedPermitOut] = Field(default_factory=list)
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
        selected_permits: list | None = None,
    ) -> "ProjectOut":
        return ProjectOut(
            id=project.project_no,
            projectNo=project.project_no,
            projectName=project.project_name,
            description=project.description,
            scopeClientConfirmedAt=project.scope_client_confirmed_at,
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
            selectedPermits=[SelectedPermitOut.from_model(p) for p in (selected_permits or [])],
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
    # Set once the client's signed confirmation of this scope has been
    # uploaded (see project_service.confirm_requirement_scope) -- the
    # sole sign-off required to leave the Requirement stage (migration
    # 0079 dropped the earlier staff-only internal-approval step).
    scopeClientConfirmedAt: datetime | None = None
    revisions: list[ScopeRevisionOut] = Field(default_factory=list)


class HandoverChecklistItemOut(BaseModel):
    id: str
    sourceType: str
    title: str
    completedAt: datetime

    @staticmethod
    def from_model(item) -> "HandoverChecklistItemOut":
        return HandoverChecklistItemOut(
            id=str(item.id), sourceType=item.source_type, title=item.title, completedAt=item.completed_at,
        )


class HandoverStatusOut(BaseModel):
    """The project's own hand-over readiness/acknowledgment pair --
    handoverSentAt is set once project_service.notify_handover_ready
    has flagged the project ready (every track closed, fully paid);
    the frontend uses it to decide whether the "Confirm Hand-over"
    signed-document upload action is available yet."""

    handoverSentAt: datetime | None = None
    handoverAcknowledgedAt: datetime | None = None
    checklist: list[HandoverChecklistItemOut] = Field(default_factory=list)

    @staticmethod
    def from_model(project, checklist: list) -> "HandoverStatusOut":
        return HandoverStatusOut(
            handoverSentAt=project.handover_sent_at,
            handoverAcknowledgedAt=project.handover_acknowledged_at,
            checklist=[HandoverChecklistItemOut.from_model(item) for item in checklist],
        )


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
    # Permits this project needs to apply for (migration 0073, picked
    # via PermitPickerDialog) -- becomes the Permit track's own
    # trackable ProjectSelectedPermit rows. Distinct from
    # requiredPermitDocuments below, which is about permits the client
    # already holds.
    selectedPermits: list[SelectedPermitIn] | None = None
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


class CloseDesignActivityRequest(BaseModel):
    status: str = "Complete"

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        if value not in ("Complete", "Cancelled"):
            raise ValueError("status must be 'Complete' or 'Cancelled'")
        return value


class SetPermitStatusRequest(BaseModel):
    """Permits have no sub-tasks -- the user sets this directly at
    their own discretion (migration 0073), unlike Design's auto-close.
    'Eligible' isn't settable here: it's computed
    (project_service._recompute_permit_eligibility)."""

    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        if value not in ("In Progress", "Complete", "Cancelled"):
            raise ValueError("status must be 'In Progress', 'Complete', or 'Cancelled'")
        return value


class SetSupervisionStatusRequest(BaseModel):
    """Same shape as SetPermitStatusRequest -- Supervision also has no
    sub-tasks (migration 0074), the user sets this directly based on
    their own read of site-engineer reports."""

    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, value: str) -> str:
        if value not in ("In Progress", "Complete", "Cancelled"):
            raise ValueError("status must be 'In Progress', 'Complete', or 'Cancelled'")
        return value


