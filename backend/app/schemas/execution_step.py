from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionStepTemplateOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    weightPercentage: float

    @staticmethod
    def from_model(step) -> "ExecutionStepTemplateOut":
        return ExecutionStepTemplateOut(
            id=f"EST-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
        )


class ExecutionStepTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    weightPercentage: float = Field(gt=0, le=100)


class ExecutionStepTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    weightPercentage: float | None = Field(default=None, gt=0, le=100)


class ExecutionStepMoveRequest(BaseModel):
    direction: str = Field(pattern="^(up|down)$")


class ProjectExecutionStepOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    weightPercentage: float
    status: str
    completedAt: datetime | None
    completedByName: str | None

    @staticmethod
    def from_model(step, completed_by_name: str | None) -> "ProjectExecutionStepOut":
        return ProjectExecutionStepOut(
            id=f"PES-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            weightPercentage=float(step.weight_percentage),
            status=step.status,
            completedAt=step.completed_at,
            completedByName=completed_by_name,
        )
