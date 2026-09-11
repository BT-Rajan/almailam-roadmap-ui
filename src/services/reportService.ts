import { apiClient } from '@/services/httpClient'
import type {
  ChartDataPoint,
  ClientWithProjects,
  EmployeePerformance,
  FinancialPeriodSummary,
  LineChartData,
  PaymentLedgerEntry,
  PaymentProjections,
  ReportMetric,
  ReportSection,
} from '@/types/Report'

export interface PaymentLedgerFilter {
  projectNo?: string
  clientId?: string
  startDate?: string
  endDate?: string
}

async function getSummary(): Promise<ReportMetric[]> {
  return apiClient.get<ReportMetric[]>('/api/reports/summary')
}

async function getProjectsByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/projects-by-status')
}

async function getProjectsByPriority(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/projects-by-priority')
}

async function getTasksByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/tasks-by-status')
}

async function getTasksByPriority(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/tasks-by-priority')
}

async function getSubmissionsByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/submissions-by-status')
}

async function getQuotationsByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/quotations-by-status')
}

async function getContractsByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/contracts-by-status')
}

async function getDocumentsByStatus(): Promise<ChartDataPoint[]> {
  return apiClient.get<ChartDataPoint[]>('/api/reports/documents-by-status')
}

async function getPaymentsReceivedByMonth(months = 6): Promise<LineChartData[]> {
  return apiClient.get<LineChartData[]>(`/api/reports/payments-received-by-month?months=${months}`)
}

async function getProjectReport(projectNo: string): Promise<ReportSection[]> {
  return apiClient.get<ReportSection[]>(`/api/reports/projects/${projectNo}`)
}

async function getClientsWithProjects(): Promise<ClientWithProjects[]> {
  return apiClient.get<ClientWithProjects[]>('/api/reports/clients-projects')
}

function buildLedgerQuery(filter: PaymentLedgerFilter): string {
  const params = new URLSearchParams()
  if (filter.projectNo) params.set('projectNo', filter.projectNo)
  if (filter.clientId) params.set('clientId', filter.clientId)
  if (filter.startDate) params.set('startDate', filter.startDate)
  if (filter.endDate) params.set('endDate', filter.endDate)
  const queryString = params.toString()
  return queryString ? `?${queryString}` : ''
}

async function getPaymentLedger(filter: PaymentLedgerFilter = {}): Promise<PaymentLedgerEntry[]> {
  return apiClient.get<PaymentLedgerEntry[]>(`/api/reports/payment-ledger${buildLedgerQuery(filter)}`)
}

async function getPaymentProjections(filter: Pick<PaymentLedgerFilter, 'projectNo' | 'clientId'> = {}): Promise<PaymentProjections> {
  return apiClient.get<PaymentProjections>(`/api/reports/payment-projections${buildLedgerQuery(filter)}`)
}

async function getEmployeePerformance(year: number, month: number): Promise<EmployeePerformance[]> {
  return apiClient.get<EmployeePerformance[]>(`/api/reports/employee-performance?year=${year}&month=${month}`)
}

async function getFinancialSummary(startDate: string, endDate: string): Promise<FinancialPeriodSummary> {
  return apiClient.get<FinancialPeriodSummary>(`/api/reports/financial-summary?startDate=${startDate}&endDate=${endDate}`)
}

export const reportService = {
  getSummary,
  getProjectsByStatus,
  getProjectsByPriority,
  getTasksByStatus,
  getTasksByPriority,
  getSubmissionsByStatus,
  getQuotationsByStatus,
  getContractsByStatus,
  getDocumentsByStatus,
  getPaymentsReceivedByMonth,
  getProjectReport,
  getClientsWithProjects,
  getPaymentLedger,
  getPaymentProjections,
  getEmployeePerformance,
  getFinancialSummary,
}
