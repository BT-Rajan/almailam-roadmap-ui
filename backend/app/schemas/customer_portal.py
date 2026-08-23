from datetime import date

from pydantic import BaseModel


class CustomerProjectOption(BaseModel):
    """One project a logged-in customer can view -- returned by GET
    /api/customer-portal/projects so the frontend can auto-redirect when
    there's exactly one, or show a picker when there's more than one."""

    projectId: str
    projectName: str


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


class ProjectActivityGroup(BaseModel):
    serviceName: str
    activities: list[str]


class UpcomingPayment(BaseModel):
    description: str
    amountDue: float
    amountReceived: float
    dueDate: date


class ProjectBudget(BaseModel):
    contractAmount: float
    currency: str
    totalPaid: float
    totalDue: float
    upcomingPayments: list[UpcomingPayment]


class CustomerProjectView(BaseModel):
    project: CustomerProjectStatus
    milestones: list[ProjectMilestone]
    deliverables: list[ProjectDeliverable]
    updates: list[ProjectUpdate]
    activities: list[ProjectActivityGroup]
    budget: ProjectBudget | None = None
