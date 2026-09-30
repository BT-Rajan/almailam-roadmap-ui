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


class PaymentLedgerEntry(BaseModel):
    entryType: str = "Payment"
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
    overdue: float = 0


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


class FinancialCurrencyBreakdown(BaseModel):
    currency: str
    totalReceived: float
    totalRefunded: float = 0
    netReceived: float = 0
    totalDue: float
    totalCollected: float = 0
    totalOutstanding: float
    totalOverdue: float


class FinancialPeriodSummary(BaseModel):
    startDate: str
    endDate: str
    paymentCount: int
    byCurrency: list[FinancialCurrencyBreakdown]
