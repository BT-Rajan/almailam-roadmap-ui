import { apiClient } from '@/services/httpClient'
import type { ChartDataPoint, LineChartData, ReportMetric, ReportSection } from '@/types/Report'

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
}
