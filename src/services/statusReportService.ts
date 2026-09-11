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

// Every report (Pending or Attached) filed against one project -- backs
// the read-only calendar on that project's own Supervision > Documents
// tab, distinct from getInbox above (the recipient's cross-project
// review queue).
async function getForProject(projectNo: string): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>(`/api/status-reports/project/${projectNo}`)
}

// Every report attached to one specific task -- backs the "task
// history" shown on a Design/Permit/Supervision task once it's
// assigned to a site engineer.
async function getForTask(taskNo: string): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>(`/api/status-reports/task/${taskNo}`)
}

export const statusReportService = { getInbox, attachReport, getForProject, getForTask }
