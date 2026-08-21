from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalProcessWaiveRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ProjectApprovalStepOut(BaseModel):
    id: str
    name: str
    stageKey: str
    sequenceNumber: int
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
    ) -> "ProjectApprovalStepOut":
        return ProjectApprovalStepOut(
            id=f"PAS-{step.id:03d}",
            name=step.name,
            stageKey=step.stage_key,
            sequenceNumber=step.sequence_number,
            isOptional=step.is_optional,
            status=step.status,
            completedAt=step.completed_at,
            completedByName=completed_by_name,
            waivedAt=step.waived_at,
            waivedByName=waived_by_name,
            waivedReason=step.waived_reason,
        )
