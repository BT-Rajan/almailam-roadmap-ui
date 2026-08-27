import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/httpClient'
import type { GovernmentSubmission, ResponseOutcome, SubmissionFollowup, SubmissionStatus } from '@/types/Submission'

/**
 * Fetch all government submissions from backend API
 */
async function getSubmissions(): Promise<GovernmentSubmission[]> {
  try {
    return await apiClient.get<GovernmentSubmission[]>('/api/submissions')
  } catch (error) {
    console.error('Failed to fetch submissions:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch submissions')
  }
}

/**
 * Fetch government submissions for a specific project from backend API
 */
async function getSubmissionsByProject(projectId: string): Promise<GovernmentSubmission[]> {
  try {
    return await apiClient.get<GovernmentSubmission[]>(`/api/submissions?projectId=${projectId}`)
  } catch (error) {
    console.error(`Failed to fetch submissions for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch submissions')
  }
}

export interface SubmissionCreateInput {
  projectId: string
  authorityId: string
  formId: string
  expectedDecisionDate?: string
  notes?: string
}

/**
 * Create a new government submission via backend API
 */
async function createSubmission(submissionData: SubmissionCreateInput): Promise<GovernmentSubmission> {
  try {
    return await apiClient.post<GovernmentSubmission>('/api/submissions', submissionData)
  } catch (error) {
    console.error('Failed to create submission:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create submission')
  }
}

/**
 * Update a government submission's editable fields (expected decision date,
 * notes) via backend API. Does NOT change status -- use setSubmissionStatus
 * for that, which goes through the real state-machine-enforced endpoint.
 */
async function updateSubmission(
  submissionId: string,
  submissionData: { expectedDecisionDate?: string; notes?: string },
): Promise<GovernmentSubmission> {
  try {
    return await apiClient.patch<GovernmentSubmission>(`/api/submissions/${submissionId}`, submissionData)
  } catch (error) {
    console.error(`Failed to update submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update submission')
  }
}

/**
 * Move a submission to a new status (Submitted, Under Review, Approved,
 * Rejected, Withdrawn, ...) via the backend's state-machine-enforced
 * status endpoint. A reason is required for Rejected, Comments Received,
 * and Withdrawn -- the backend validates this and returns a 422 if it's
 * missing, or if the transition itself isn't a valid one from the
 * submission's current status.
 */
async function setSubmissionStatus(
  submissionId: string,
  status: SubmissionStatus,
  reason?: string,
): Promise<GovernmentSubmission> {
  try {
    return await apiClient.patch<GovernmentSubmission>(`/api/submissions/${submissionId}/status`, {
      status,
      reason,
    })
  } catch (error) {
    console.error(`Failed to update status for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update submission status')
  }
}

/**
 * Shared multipart upload helper -- same 401-retry-once + error-shape
 * handling as documentService's uploadDocument/addVersion, since apiClient
 * always JSON-encodes its body and can't be used for file uploads.
 */
async function uploadMultipart<T>(path: string, formData: FormData): Promise<T> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch(path, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) {
    const data = await response.json().catch(() => undefined)
    throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
  }
  return (await response.json()) as T
}

async function downloadFile(path: string): Promise<Blob> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch(path, {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) {
    throw new Error(`Download failed with status ${response.status}`)
  }
  return await response.blob()
}

/**
 * Upload/replace the file behind one Required Documents checklist entry --
 * backend only allows this while the submission is in Draft.
 */
async function uploadDocument(submissionId: string, documentId: number, file: File): Promise<GovernmentSubmission> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    return await uploadMultipart<GovernmentSubmission>(
      `/api/submissions/${submissionId}/documents/${documentId}/upload`,
      formData,
    )
  } catch (error) {
    console.error(`Failed to upload document ${documentId} for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload document')
  }
}

async function downloadDocument(submissionId: string, documentId: number): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/documents/${documentId}/download`)
}

/**
 * Upload proof the form was actually handed to the authority. Backend
 * requires every required document to be Uploaded/Verified first and
 * moves the submission Draft -> Submitted as a side effect.
 */
async function uploadProofOfSubmission(submissionId: string, file: File): Promise<GovernmentSubmission> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    return await uploadMultipart<GovernmentSubmission>(`/api/submissions/${submissionId}/proof-of-submission`, formData)
  } catch (error) {
    console.error(`Failed to upload proof of submission for ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload proof of submission')
  }
}

async function downloadProofOfSubmission(submissionId: string): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/proof-of-submission/download`)
}

/**
 * Upload proof of the authority's response, along with the outcome it
 * conveys (Approved/Rejected). Doesn't change status by itself.
 */
async function uploadProofOfResponse(
  submissionId: string,
  file: File,
  outcome: ResponseOutcome,
): Promise<GovernmentSubmission> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('outcome', outcome)
    return await uploadMultipart<GovernmentSubmission>(`/api/submissions/${submissionId}/proof-of-response`, formData)
  } catch (error) {
    console.error(`Failed to upload proof of response for ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to upload proof of response')
  }
}

async function downloadProofOfResponse(submissionId: string): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/proof-of-response/download`)
}

/**
 * Marks the submission complete (-> Approved) -- only valid once an
 * Approved outcome has been recorded against an uploaded proof of response.
 */
async function markComplete(submissionId: string): Promise<GovernmentSubmission> {
  try {
    return await apiClient.post<GovernmentSubmission>(`/api/submissions/${submissionId}/complete`, {})
  } catch (error) {
    console.error(`Failed to mark submission ${submissionId} complete:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to mark submission complete')
  }
}

async function getFollowups(submissionId: string): Promise<SubmissionFollowup[]> {
  try {
    return await apiClient.get<SubmissionFollowup[]>(`/api/submissions/${submissionId}/followups`)
  } catch (error) {
    console.error(`Failed to fetch follow-ups for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch follow-ups')
  }
}

export interface FollowupCreateInput {
  followupDate: string
  followupTime: string
  contactPerson: string
  notes?: string
}

async function addFollowup(submissionId: string, payload: FollowupCreateInput): Promise<SubmissionFollowup> {
  try {
    return await apiClient.post<SubmissionFollowup>(`/api/submissions/${submissionId}/followups`, payload)
  } catch (error) {
    console.error(`Failed to record follow-up for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record follow-up')
  }
}

export const governmentSubmissionService = {
  getSubmissions,
  getSubmissionsByProject,
  createSubmission,
  updateSubmission,
  setSubmissionStatus,
  uploadDocument,
  downloadDocument,
  uploadProofOfSubmission,
  downloadProofOfSubmission,
  uploadProofOfResponse,
  downloadProofOfResponse,
  markComplete,
  getFollowups,
  addFollowup,
}
