"""Response shapes for the date-ranged reports (see services/report_period.py)."""

from typing import Literal

from pydantic import BaseModel


class PeriodOut(BaseModel):
    startDate: str
    endDate: str


class LabelValueOut(BaseModel):
    label: str
    value: float


class ExecutiveKpisOut(BaseModel):
    newProjects: int
    projectsCompleted: int
    activeProjectsNow: int
    onHoldProjectsNow: int
    newClients: int
    contractsSigned: int
    contractsSignedValue: float
    cashReceived: float
    refunded: float
    netCash: float
    billed: float
    collectedOfBilled: float
    collectionRate: float | None
    outstandingNow: float
    overdueNow: float
    tasksCompleted: int
    tasksOnTimeRate: float | None
    openTasksNow: int
    overdueTasksNow: int


class CashFlowOut(BaseModel):
    categories: list[str]
    received: list[float]
    billed: list[float]


class ProjectFlowOut(BaseModel):
    categories: list[str]
    started: list[int]
    completed: list[int]


class TopClientOut(BaseModel):
    clientName: str
    received: float
    payments: int


class ProjectInfoOut(BaseModel):
    projectNo: str
    projectName: str
    clientName: str
    engineer: str
    status: str
    currentStage: str


class ScheduleOut(BaseModel):
    startDate: str
    targetDate: str
    totalDays: int
    timeElapsedPercent: float
    progressPercent: int
    daysToTarget: int
    health: Literal["on-track", "at-risk", "late", "completed", "cancelled", "on-hold"]


class OverdueTaskOut(BaseModel):
    taskNo: str
    title: str
    assignee: str
    dueDate: str
    daysLate: int


class ProjectTasksOut(BaseModel):
    byStatus: list[LabelValueOut]
    total: int
    open: int
    overdue: int
    completedInPeriod: int
    onTimeRate: float | None
    overdueList: list[OverdueTaskOut]


class StreamMoneyOut(BaseModel):
    stream: str
    currency: str
    contractAmount: float
    received: float
    outstanding: float
    overdue: float
    receivedInPeriod: float
    billedInPeriod: float


class UpcomingInstalmentOut(BaseModel):
    stream: str
    description: str
    dueDate: str
    amountDue: float
    outstanding: float
    currency: str
    overdue: bool


class ProjectMoneyOut(BaseModel):
    streams: list[StreamMoneyOut]
    chartCurrency: str | None
    cashFlow: CashFlowOut
    upcoming: list[UpcomingInstalmentOut]


class ProjectPerformanceOut(BaseModel):
    period: PeriodOut
    bucket: Literal["week", "month", "year"]
    project: ProjectInfoOut
    schedule: ScheduleOut
    tasks: ProjectTasksOut
    money: ProjectMoneyOut
    documents: list[LabelValueOut]
    submissions: list[LabelValueOut]


class WorkloadMemberOut(BaseModel):
    userId: str
    name: str
    role: str
    inactive: bool
    activeProjects: int
    openTasks: int
    overdueTasks: int
    dueSoonTasks: int
    laterTasks: int
    notStartedTasks: int
    oldestOverdueDays: int | None
    completedInPeriod: int
    onTimeRate: float | None


class WorkloadTotalsOut(BaseModel):
    people: int
    peopleWithOpenWork: int
    peopleWithOverdue: int
    openTasks: int
    overdueTasks: int
    overdueShare: float | None
    dueSoonTasks: int
    completedInPeriod: int
    onTimeRate: float | None
    strandedTasks: int


class TeamWorkloadOut(BaseModel):
    period: PeriodOut
    dueSoonDays: int
    totals: WorkloadTotalsOut
    members: list[WorkloadMemberOut]


class ExecutiveSummaryOut(BaseModel):
    period: PeriodOut
    bucket: Literal["week", "month", "year"]
    currency: str
    kpis: ExecutiveKpisOut
    cashFlow: CashFlowOut
    projectFlow: ProjectFlowOut
    projectStatusNow: list[LabelValueOut]
    topClients: list[TopClientOut]
