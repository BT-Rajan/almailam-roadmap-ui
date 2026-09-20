import { apiClient, asError } from '@/services/httpClient'
import type { ScheduledReport, ScheduledReportInput } from '@/types/ScheduledReport'

async function getSchedules(): Promise<ScheduledReport[]> {
  try {
    return await apiClient.get<ScheduledReport[]>('/api/scheduled-reports')
  } catch (error) {
    console.error('Failed to fetch scheduled reports:', error)
    throw asError(error, 'Failed to fetch scheduled reports')
  }
}

async function createSchedule(payload: ScheduledReportInput): Promise<ScheduledReport> {
  try {
    return await apiClient.post<ScheduledReport>('/api/scheduled-reports', payload)
  } catch (error) {
    console.error('Failed to create scheduled report:', error)
    throw asError(error, 'Failed to create scheduled report')
  }
}

async function updateSchedule(id: string, payload: ScheduledReportInput): Promise<ScheduledReport> {
  try {
    return await apiClient.patch<ScheduledReport>(`/api/scheduled-reports/${id}`, payload)
  } catch (error) {
    console.error(`Failed to update scheduled report ${id}:`, error)
    throw asError(error, 'Failed to update scheduled report')
  }
}

async function deleteSchedule(id: string): Promise<void> {
  try {
    await apiClient.delete(`/api/scheduled-reports/${id}`)
  } catch (error) {
    console.error(`Failed to delete scheduled report ${id}:`, error)
    throw asError(error, 'Failed to delete scheduled report')
  }
}

async function sendTestNow(id: string): Promise<void> {
  try {
    await apiClient.post(`/api/scheduled-reports/${id}/send-test`, {})
  } catch (error) {
    console.error(`Failed to send test for scheduled report ${id}:`, error)
    throw asError(error, 'Failed to send test report')
  }
}

export const scheduledReportService = {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  sendTestNow,
}
