from datetime import datetime

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


class ExecutionStepWaiveRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ProjectExecutionStepOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    weightPercentage: float
    stageKey: str
    isOptional: bool
    status: str
    completedAt: datetime | None
    completedByName: str | None
    waivedAt: datetime | None
    waivedByName: str | None
    waivedReason: str | None

    @staticmethod
    def from_model(
        step, completed_by_name: str | None, waived_by_name: str | None = None
    ) -> "ProjectExecutionStepOut":
        return ProjectExecutionStepOut(
            id=f"PES-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
            stageKey=step.stage_key,
            isOptional=step.is_optional,
            status=step.status,
            completedAt=step.completed_at,
            completedByName=completed_by_name,
            waivedAt=step.waived_at,
            waivedByName=waived_by_name,
            waivedReason=step.waived_reason,
        )
