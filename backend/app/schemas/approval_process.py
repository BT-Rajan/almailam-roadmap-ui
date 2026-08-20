from datetime import datetime

from pydantic import BaseModel


class ProjectApprovalStepOut(BaseModel):
    id: str
    name: str
    sequenceNumber: int
    status: str
    completedAt: datetime | None
    completedByName: str | None

    @staticmethod
    def from_model(step, completed_by_name: str | None) -> "ProjectApprovalStepOut":
        return ProjectApprovalStepOut(
            id=f"PAS-{step.id:03d}",
            name=step.name,
            sequenceNumber=step.sequence_number,
            status=step.status,
            completedAt=step.completed_at,
            completedByName=completed_by_name,
        )
