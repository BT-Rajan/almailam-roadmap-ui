import { apiClient } from '@/services/httpClient'
import type { EngineerProjectOption, StatusReport, StatusReportSupervisionType } from '@/types/StatusReport'

export interface StatusReportFileInput {
  projectId: string
  receiptType?: string
  supervisionType: StatusReportSupervisionType
  notes: string
}

async function getMyProjects(): Promise<EngineerProjectOption[]> {
  return apiClient.get<EngineerProjectOption[]>('/api/site-portal/projects')
}

async function getTodaysReport(): Promise<StatusReport | null> {
  return apiClient.get<StatusReport | null>('/api/site-portal/reports/today')
}

async function fileTodaysReport(input: StatusReportFileInput): Promise<StatusReport> {
  return apiClient.post<StatusReport>('/api/site-portal/reports/today', input)
}

async function getMyReports(start: string, end: string): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>(`/api/site-portal/reports?start=${start}&end=${end}`)
}

export const sitePortalService = { getMyProjects, getTodaysReport, fileTodaysReport, getMyReports }
