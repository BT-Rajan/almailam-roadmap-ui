from pydantic import BaseModel


class ChartDataPoint(BaseModel):
    label: str
    value: float
    color: str | None = None


class LineChartDataPoint(BaseModel):
    x: str
    value: float
    color: str | None = None


class ReportMetricChange(BaseModel):
    direction: str
    percentage: float


class ReportMetric(BaseModel):
    label: str
    value: str | float
    unit: str | None = None
    change: ReportMetricChange | None = None
    color: str | None = None


class ReportSection(BaseModel):
    title: str
    description: str | None = None
    metrics: list[ReportMetric] | None = None


class ClientProjectSummary(BaseModel):
    projectNo: str
    projectName: str
    status: str
    currentStage: str
    progress: int


class ClientWithProjects(BaseModel):
    clientId: str
    clientName: str
    clientStatus: str
    projects: list[ClientProjectSummary]


class PaymentLedgerEntry(BaseModel):
    paymentNo: str
    date: str
    projectNo: str
    projectName: str
    clientName: str
    service: str
    amount: float
    currency: str
    mode: str
    reference: str | None = None
    payer: str


class ProjectionByMonth(BaseModel):
    month: str
    amount: float


class ProjectionByProject(BaseModel):
    projectNo: str
    projectName: str
    amount: float


class ProjectionByService(BaseModel):
    service: str
    amount: float


class PaymentProjections(BaseModel):
    byMonth: list[ProjectionByMonth]
    byProject: list[ProjectionByProject]
    byService: list[ProjectionByService]


class EmployeePerformance(BaseModel):
    userId: str
    employeeName: str
    assigned: int
    completed: int
    completionRate: int
