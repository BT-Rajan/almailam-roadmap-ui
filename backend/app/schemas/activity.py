from pydantic import BaseModel


class ActivityRecordOut(BaseModel):
    id: str
    type: str
    entityType: str
    entityId: str
    entityName: str
    projectId: str | None = None
    projectName: str | None = None
    userId: str
    userName: str
    description: str
    timestamp: str


class DailySummaryOut(BaseModel):
    date: str
    new: int
    updated: int
    delayed: int
    completed: int
    assigned: int
    commented: int
    approved: int
    rejected: int
    total: int
    activities: list[ActivityRecordOut]


class FilterOptionOut(BaseModel):
    id: str
    name: str
