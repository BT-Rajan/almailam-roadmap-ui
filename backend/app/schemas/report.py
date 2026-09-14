from pydantic import BaseModel


class ChartDataPoint(BaseModel):
    label: str
    value: float
    color: str | None = None


class LineChartDataPoint(BaseModel):
    x: str
    value: float
    color: str | None = None


class PaymentsReceivedByMonth(BaseModel):
    currency: str
    series: list[LineChartDataPoint]


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
    currency: str
    amount: float


class ProjectionByProject(BaseModel):
    projectNo: str
    projectName: str
    currency: str
    amount: float


class ProjectionByService(BaseModel):
    service: str
    currency: str
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


class TeamWorkloadMember(BaseModel):
    userId: str
    name: str
    role: str
    activeProjects: int
    activeTasks: int
    overdueTasks: int
    allocationPercent: int
    overallocated: bool


class TeamWorkload(BaseModel):
    members: list[TeamWorkloadMember]
    totalMembers: int
    averageUtilization: int
    overallocatedCount: int
    capacityAvailable: int


class FinancialCurrencyBreakdown(BaseModel):
    currency: str
    totalReceived: float
    totalDue: float
    totalOutstanding: float
    totalOverdue: float


class FinancialPeriodSummary(BaseModel):
    startDate: str
    endDate: str
    paymentCount: int
    byCurrency: list[FinancialCurrencyBreakdown]
