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

async function getTodaysReports(): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>('/api/site-portal/reports/today')
}

async function fileTodaysReport(input: StatusReportFileInput): Promise<StatusReport> {
  return apiClient.post<StatusReport>('/api/site-portal/reports/today', input)
}

async function getMyReports(start: string, end: string): Promise<StatusReport[]> {
  return apiClient.get<StatusReport[]>(`/api/site-portal/reports?start=${start}&end=${end}`)
}

async function uploadReportImage(reportId: string, file: File): Promise<StatusReport> {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.postForm<StatusReport>(`/api/site-portal/reports/${reportId}/images`, formData)
}

async function deleteReportImage(reportId: string, imageId: string): Promise<StatusReport> {
  return apiClient.delete<StatusReport>(`/api/site-portal/reports/${reportId}/images/${imageId}`)
}

async function getReportImageBlob(reportId: string, imageId: string): Promise<Blob> {
  return apiClient.getBlob(`/api/site-portal/reports/${reportId}/images/${imageId}/file`)
}

export const sitePortalService = {
  getMyProjects,
  getTodaysReports,
  fileTodaysReport,
  getMyReports,
  uploadReportImage,
  deleteReportImage,
  getReportImageBlob,
}
