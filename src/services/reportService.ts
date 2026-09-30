import { apiClient } from '@/services/httpClient'
import type {
  ChartDataPoint,
  ClientWithProjects,
  EmployeePerformance,
  EmployeeActivityReport,
  ExecutiveSummary,
  ProjectPerformance,
  FinancialPeriodSummary,
  PaymentLedgerEntry,
  PaymentProjections,
  PaymentsReceivedByMonth,
  ReportMetric,
  TeamWorkloadReport,
} from '@/types/Report'
import type { DateRange } from '@/utils/reportRange'

interface PaymentLedgerFilter {
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

async function getPaymentsReceivedByMonth(months = 6): Promise<PaymentsReceivedByMonth> {
  return apiClient.get<PaymentsReceivedByMonth>(`/api/reports/payments-received-by-month?months=${months}`)
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

async function getTeamWorkload(range: DateRange): Promise<TeamWorkloadReport> {
  return apiClient.get<TeamWorkloadReport>(`/api/reports/team-workload?${periodQuery(range)}`)
}

function periodQuery(range: DateRange): string {
  return new URLSearchParams({ startDate: range.from, endDate: range.to }).toString()
}

async function getExecutiveSummary(range: DateRange): Promise<ExecutiveSummary> {
  return apiClient.get<ExecutiveSummary>(`/api/reports/executive?${periodQuery(range)}`)
}

async function getEmployeeActivity(range: DateRange, userId?: string): Promise<EmployeeActivityReport> {
  const query = periodQuery(range) + (userId ? `&userId=${encodeURIComponent(userId)}` : '')
  return apiClient.get<EmployeeActivityReport>(`/api/reports/employee-activity?${query}`)
}

async function getProjectPerformance(projectNo: string, range: DateRange): Promise<ProjectPerformance> {
  return apiClient.get<ProjectPerformance>(`/api/reports/project-performance/${encodeURIComponent(projectNo)}?${periodQuery(range)}`)
}

export const reportService = {
  getSummary,
  getProjectsByStatus,
  getTasksByStatus,
  getTasksByPriority,
  getSubmissionsByStatus,
  getQuotationsByStatus,
  getContractsByStatus,
  getDocumentsByStatus,
  getPaymentsReceivedByMonth,
  getClientsWithProjects,
  getPaymentLedger,
  getPaymentProjections,
  getEmployeePerformance,
  getFinancialSummary,
  getTeamWorkload,
  getExecutiveSummary,
  getProjectPerformance,
  getEmployeeActivity,
}
