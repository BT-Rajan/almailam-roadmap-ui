from typing import Literal

from pydantic import BaseModel, Field


class WorkflowStageOut(BaseModel):
    id: str
    name: str
    description: str

    @staticmethod
    def from_model(stage) -> "WorkflowStageOut":
        return WorkflowStageOut(
            id=f"STG-{stage.id:03d}",
            name=stage.name,
            description=stage.description or "",
        )


class WorkflowTemplateOut(BaseModel):
    id: str
    name: str
    isDefault: bool
    stages: list[WorkflowStageOut]

    @staticmethod
    def from_model(template) -> "WorkflowTemplateOut":
        return WorkflowTemplateOut(
            id=f"WFT-{template.id:03d}",
            name=template.name,
            isDefault=template.is_default,
            stages=[WorkflowStageOut.from_model(s) for s in template.stages],
        )


class WorkflowStageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class WorkflowStageUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class WorkflowStageMove(BaseModel):
    direction: Literal["up", "down"]
