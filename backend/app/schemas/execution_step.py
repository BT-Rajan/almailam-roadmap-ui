from pydantic import BaseModel, Field


class ExecutionStepSetOut(BaseModel):
    id: str
    name: str
    description: str | None

    @staticmethod
    def from_model(step_set) -> "ExecutionStepSetOut":
        return ExecutionStepSetOut(
            id=f"ESS-{step_set.id:03d}",
            name=step_set.name,
            description=step_set.description,
        )


class ExecutionStepSetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class ExecutionStepSetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class ExecutionStepTemplateOut(BaseModel):
    id: str
    stepSetId: str
    name: str
    sequenceNumber: int
    weightPercentage: float
    stageKey: str
    isOptional: bool
    triggerKey: str | None

    @staticmethod
    def from_model(step) -> "ExecutionStepTemplateOut":
        return ExecutionStepTemplateOut(
            id=f"EST-{step.id:03d}",
            stepSetId=f"ESS-{step.step_set_id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
            stageKey=step.stage_key,
            isOptional=step.is_optional,
            triggerKey=step.trigger_key,
        )


class ExecutionStepTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    weightPercentage: float = Field(gt=0, le=100)
    stageKey: str = Field(min_length=1, max_length=40)
    isOptional: bool = False
    # '' means "no trigger" -- see execution_step_service._normalize_trigger_key.
    triggerKey: str = Field(default="", max_length=60)


class ExecutionStepTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    weightPercentage: float | None = Field(default=None, gt=0, le=100)
    stageKey: str | None = Field(default=None, min_length=1, max_length=40)
    isOptional: bool | None = None
    # None (the default) means "this PATCH doesn't touch triggerKey" --
    # send '' to explicitly clear it. See _normalize_trigger_key.
    triggerKey: str | None = Field(default=None, max_length=60)


class ExecutionStepMoveRequest(BaseModel):
    direction: str = Field(pattern="^(up|down)$")


class ExecutionStepProgressUpdate(BaseModel):
    completionPercentage: int = Field(ge=0, le=100)
    remarks: str | None = Field(default=None, max_length=2000)


class ExecutionStepBulkItem(BaseModel):
    id: str
    completionPercentage: int = Field(ge=0, le=100)
    remarks: str | None = Field(default=None, max_length=2000)
    isExcluded: bool = False
    excludedReason: str | None = Field(default=None, max_length=200)


class ExecutionStepBulkUpdate(BaseModel):
    steps: list[ExecutionStepBulkItem]


class ProjectCustomStepCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    weightPercentage: float = Field(gt=0, le=100)
    stageKey: str = Field(min_length=1, max_length=40)


class ProjectExecutionStepOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    weightPercentage: float
    stageKey: str
    isOptional: bool
    isExcluded: bool
    excludedReason: str | None
    completionPercentage: int
    remarks: str | None
    isAdditionalScope: bool = False
    contractCovered: bool | None = None
    triggerKey: str | None = None
    isCustom: bool = False

    @staticmethod
    def from_model(step) -> "ProjectExecutionStepOut":
        return ProjectExecutionStepOut(
            id=f"PES-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
            stageKey=step.stage_key,
            isOptional=step.is_optional,
            isExcluded=step.is_excluded,
            excludedReason=step.excluded_reason,
            completionPercentage=step.completion_percentage,
            remarks=step.remarks,
            isAdditionalScope=step.is_additional_scope,
            contractCovered=step.contract_covered,
            triggerKey=step.trigger_key,
            isCustom=step.is_custom,
        )
