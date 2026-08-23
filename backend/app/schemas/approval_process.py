from datetime import datetime

from pydantic import BaseModel


class ProjectApprovalStepOut(BaseModel):
    id: str
    name: str
    stageKey: str
    sequenceNumber: int
    hasDocument: bool
    originalFilename: str | None
    fileSizeBytes: int | None
    uploadedAt: datetime | None
    uploadedByName: str | None
    # True once either completion path has fired: hasDocument (a gate
    # review document was uploaded) or completedAt (tagged documents
    # were approved and a user confirmed completion). Use this, not
    # hasDocument, for "is this stage done".
    isComplete: bool
    completedAt: datetime | None
    completedByName: str | None

    @staticmethod
    def from_model(
        step, uploaded_by_name: str | None = None, completed_by_name: str | None = None
    ) -> "ProjectApprovalStepOut":
        return ProjectApprovalStepOut(
            id=f"PAS-{step.id:03d}",
            name=step.name,
            stageKey=step.stage_key,
            sequenceNumber=step.sequence_number,
            hasDocument=step.storage_key is not None,
            originalFilename=step.original_filename,
            fileSizeBytes=step.file_size_bytes,
            uploadedAt=step.uploaded_at,
            uploadedByName=uploaded_by_name,
            isComplete=step.storage_key is not None or step.completed_at is not None,
            completedAt=step.completed_at,
            completedByName=completed_by_name,
        )
