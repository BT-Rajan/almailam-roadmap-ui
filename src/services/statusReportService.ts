import { apiClient } from '@/services/httpClient'
import type { StatusReport } from '@/types/StatusReport'

export interface StatusReportAttachInput {
  taskId?: string
  notes: string
}

async function getInbox(): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>('/api/status-reports/inbox')
}

async function attachReport(reportId: string, input: StatusReportAttachInput): Promise<StatusReport> {
  return apiClient.post<StatusReport>(`/api/status-reports/${reportId}/attach`, input)
}

export const statusReportService = { getInbox, attachReport }
