from pydantic import BaseModel, Field


class ExecutionStepTemplateOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    weightPercentage: float
    stageKey: str
    isOptional: bool

    @staticmethod
    def from_model(step) -> "ExecutionStepTemplateOut":
        return ExecutionStepTemplateOut(
            id=f"EST-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
            stageKey=step.stage_key,
            isOptional=step.is_optional,
        )


class ExecutionStepTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    weightPercentage: float = Field(gt=0, le=100)
    stageKey: str = Field(min_length=1, max_length=40)
    isOptional: bool = False


class ExecutionStepTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    weightPercentage: float | None = Field(default=None, gt=0, le=100)
    stageKey: str | None = Field(default=None, min_length=1, max_length=40)
    isOptional: bool | None = None


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
        )
