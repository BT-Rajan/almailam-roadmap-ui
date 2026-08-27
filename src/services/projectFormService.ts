import { apiClient } from '@/services/httpClient'
import type { ProjectFormEntry, ProjectFormEntryStatus } from '@/types/Government'

async function getEntries(projectId: string): Promise<ProjectFormEntry[]> {
  return apiClient.get<ProjectFormEntry[]>(`/api/projects/${projectId}/form-entries`)
}

async function createEntry(
  projectId: string,
  formId: string,
  fieldValues: Record<string, string>,
): Promise<ProjectFormEntry> {
  return apiClient.post<ProjectFormEntry>(`/api/projects/${projectId}/form-entries`, { formId, fieldValues })
}

async function updateEntry(
  projectId: string,
  entryId: string,
  fieldValues: Record<string, string>,
): Promise<ProjectFormEntry> {
  return apiClient.patch<ProjectFormEntry>(`/api/projects/${projectId}/form-entries/${entryId}`, { fieldValues })
}

async function setEntryStatus(
  projectId: string,
  entryId: string,
  status: ProjectFormEntryStatus,
): Promise<ProjectFormEntry> {
  return apiClient.patch<ProjectFormEntry>(`/api/projects/${projectId}/form-entries/${entryId}/status`, { status })
}

async function deleteEntry(projectId: string, entryId: string): Promise<void> {
  await apiClient.delete<void>(`/api/projects/${projectId}/form-entries/${entryId}`)
}

export const projectFormService = {
  getEntries,
  createEntry,
  updateEntry,
  setEntryStatus,
  deleteEntry,
}
