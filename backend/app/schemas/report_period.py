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


class ExecutiveSummaryOut(BaseModel):
    period: PeriodOut
    bucket: Literal["week", "month", "year"]
    currency: str
    kpis: ExecutiveKpisOut
    cashFlow: CashFlowOut
    projectFlow: ProjectFlowOut
    projectStatusNow: list[LabelValueOut]
    topClients: list[TopClientOut]
