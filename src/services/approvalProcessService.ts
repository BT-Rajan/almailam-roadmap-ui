import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'

async function getProjectSteps(projectId: string): Promise<ProjectApprovalStep[]> {
  return apiClient.get<ProjectApprovalStep[]>(`/api/projects/${projectId}/approval-steps`)
}

/**
 * Upload a stage's review document -- this is what marks the stage
 * complete, there is no separate "mark complete" action. Multipart,
 * so this goes through fetch directly rather than apiClient, same
 * pattern as documentService.uploadDocument.
 */
async function uploadStageGateDocument(
  projectId: string,
  stageKey: string,
  file: File,
): Promise<ProjectApprovalStep> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)

  const doRequest = () =>
    fetch(`/api/projects/${projectId}/approval-steps/${stageKey}/document`, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) {
        response = await doRequest()
      }
    }

    if (!response.ok) {
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }

    return (await response.json()) as ProjectApprovalStep
  } catch (error) {
    console.error(`Failed to upload stage gate document for ${stageKey}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload stage gate document')
  }
}

/**
 * Download a stage's review document, same fetch-blob pattern as
 * documentService.downloadDocument.
 */
async function downloadStageGateDocument(projectId: string, stageKey: string): Promise<Blob> {
  try {
    const response = await fetch(`/api/projects/${projectId}/approval-steps/${stageKey}/document`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('almailam-access-token') || ''}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }

    return await response.blob()
  } catch (error) {
    console.error(`Failed to download stage gate document for ${stageKey}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to download stage gate document')
  }
}

/**
 * Confirms a stage is complete based on its tagged documents being
 * reviewed, instead of uploading a gate review document. No file --
 * plain POST through apiClient, unlike uploadStageGateDocument above.
 */
async function completeStageFromDocuments(projectId: string, stageKey: string): Promise<ProjectApprovalStep> {
  return apiClient.post<ProjectApprovalStep>(`/api/projects/${projectId}/approval-steps/${stageKey}/complete-from-documents`)
}

export const approvalProcessService = {
  getProjectSteps,
  uploadStageGateDocument,
  downloadStageGateDocument,
  completeStageFromDocuments,
}
