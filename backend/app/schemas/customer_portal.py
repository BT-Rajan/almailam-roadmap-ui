from datetime import date

from pydantic import BaseModel, Field


class CustomerPortalVerifyRequest(BaseModel):
    projectId: str = Field(min_length=1, max_length=20)
    mobileNumber: str = Field(min_length=1, max_length=30)


class CustomerPortalVerifyResponse(BaseModel):
    accessToken: str
    projectId: str


class CustomerProjectStatus(BaseModel):
    projectId: str
    projectName: str
    description: str
    clientName: str
    startDate: date
    expectedEndDate: date
    actualEndDate: date | None = None
    status: str
    progress: int
    summary: str
    engineerName: str
    supportEmail: str
    supportPhone: str


class ProjectMilestone(BaseModel):
    id: str
    title: str
    description: str | None = None
    dueDate: date
    status: str
    completedDate: date | None = None


class ProjectDeliverable(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: str
    status: str
    deliveryDate: date | None = None
    approvalDate: date | None = None


class ProjectUpdate(BaseModel):
    id: str
    date: date
    title: str
    description: str
    type: str


class CustomerProjectView(BaseModel):
    project: CustomerProjectStatus
    milestones: list[ProjectMilestone]
    deliverables: list[ProjectDeliverable]
    updates: list[ProjectUpdate]
