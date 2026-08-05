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
