import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/httpClient'
import type { GovernmentSubmission, SubmissionFollowup, SubmissionStage } from '@/types/Submission'

/**
 * Fetch government submissions (Permit Applications) from backend API,
 * optionally narrowed to one project and/or one stage.
 */
async function getSubmissions(projectId?: string, stage?: SubmissionStage): Promise<GovernmentSubmission[]> {
  try {
    const params = new URLSearchParams()
    if (projectId) params.set('projectId', projectId)
    if (stage) params.set('stage', stage)
    const query = params.toString()
    return await apiClient.get<GovernmentSubmission[]>(`/api/submissions${query ? `?${query}` : ''}`)
  } catch (error) {
    console.error('Failed to fetch submissions:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch submissions')
  }
}

async function getSubmission(submissionNo: string): Promise<GovernmentSubmission> {
  try {
    return await apiClient.get<GovernmentSubmission>(`/api/submissions/${submissionNo}`)
  } catch (error) {
    console.error(`Failed to fetch submission ${submissionNo}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch submission')
  }
}

export interface SubmissionCreateInput {
  projectId: string
  authorityId: string
  formId: string
  expectedDecisionDate?: string
  notes?: string
  // Optional -- links this application to one of the project's own
  // planned permits (Project.selectedPermits).
  selectedPermitId?: string
}

/**
 * Starts a new Permit Application in Prepare -- picking the type of
 * approval (authority/form) this application is for.
 */
async function createSubmission(submissionData: SubmissionCreateInput): Promise<GovernmentSubmission> {
  try {
    return await apiClient.post<GovernmentSubmission>('/api/submissions', submissionData)
  } catch (error) {
    console.error('Failed to create submission:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create submission')
  }
}

// Only the fields present are applied; an explicit null clears the
// expected decision date / notes / linked permit. authorityId + formId
// can only change while the application is still in Prepare with no
// document uploaded (the API rejects it otherwise).
export interface SubmissionUpdateInput {
  expectedDecisionDate?: string | null
  notes?: string | null
  authorityId?: string
  formId?: string
  selectedPermitId?: string | null
}

/**
 * Update a submission's own details -- doesn't change stage, that only
 * ever happens through one of the dedicated stage-advancing actions
 * below.
 */
async function updateSubmission(submissionId: string, submissionData: SubmissionUpdateInput): Promise<GovernmentSubmission> {
  try {
    return await apiClient.patch<GovernmentSubmission>(`/api/submissions/${submissionId}`, submissionData)
  } catch (error) {
    console.error(`Failed to update submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update submission')
  }
}

/**
 * Delete a permit application (soft delete server-side).
 */
async function deleteSubmission(submissionId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/submissions/${submissionId}`)
  } catch (error) {
    console.error(`Failed to delete submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete submission')
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
 * backend only allows this while the application is in Prepare.
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
 * Prepare -> Apply: every required document is Uploaded/Verified and
 * staff explicitly confirm the application is ready to file.
 */
async function confirmReadiness(submissionId: string): Promise<GovernmentSubmission> {
  try {
    return await apiClient.post<GovernmentSubmission>(`/api/submissions/${submissionId}/confirm-readiness`, {})
  } catch (error) {
    console.error(`Failed to confirm readiness for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to confirm readiness')
  }
}

export interface AcknowledgementInput {
  acknowledgementNumber?: string
  paymentReference?: string
  notes?: string
  file?: File
}

/**
 * Apply -> Track: files the application -- the authority's
 * acknowledgement number, an optional payment reference, and the
 * acknowledgement document itself.
 */
async function recordAcknowledgement(
  submissionId: string,
  input: AcknowledgementInput,
): Promise<GovernmentSubmission> {
  try {
    const formData = new FormData()
    if (input.acknowledgementNumber) formData.append('acknowledgementNumber', input.acknowledgementNumber)
    if (input.paymentReference) formData.append('paymentReference', input.paymentReference)
    if (input.notes) formData.append('notes', input.notes)
    if (input.file) formData.append('file', input.file)
    return await uploadMultipart<GovernmentSubmission>(`/api/submissions/${submissionId}/acknowledgement`, formData)
  } catch (error) {
    console.error(`Failed to record acknowledgement for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record acknowledgement')
  }
}

async function downloadAcknowledgement(submissionId: string): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/acknowledgement/download`)
}

export interface CloseApplicationInput {
  outcome: string
  closingNotes: string
  file?: File
}

/**
 * Closes the application out -- the final outcome, an optional
 * permit/decision document, and closing notes. Reachable from any stage.
 */
async function closeApplication(submissionId: string, input: CloseApplicationInput): Promise<GovernmentSubmission> {
  try {
    const formData = new FormData()
    formData.append('outcome', input.outcome)
    formData.append('closingNotes', input.closingNotes)
    if (input.file) formData.append('file', input.file)
    return await uploadMultipart<GovernmentSubmission>(`/api/submissions/${submissionId}/close`, formData)
  } catch (error) {
    console.error(`Failed to close submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to close the application')
  }
}

async function downloadPermitDocument(submissionId: string): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/permit-document/download`)
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
  file?: File
}

async function addFollowup(submissionId: string, input: FollowupCreateInput): Promise<SubmissionFollowup> {
  try {
    const formData = new FormData()
    formData.append('followupDate', input.followupDate)
    formData.append('followupTime', input.followupTime)
    formData.append('contactPerson', input.contactPerson)
    if (input.notes) formData.append('notes', input.notes)
    if (input.file) formData.append('file', input.file)
    return await uploadMultipart<SubmissionFollowup>(`/api/submissions/${submissionId}/followups`, formData)
  } catch (error) {
    console.error(`Failed to record follow-up for submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record follow-up')
  }
}

async function downloadFollowupDocument(submissionId: string, followupId: string): Promise<Blob> {
  return downloadFile(`/api/submissions/${submissionId}/followups/${followupId}/download`)
}

export const governmentSubmissionService = {
  getSubmissions,
  getSubmission,
  createSubmission,
  updateSubmission,
  deleteSubmission,
  uploadDocument,
  downloadDocument,
  confirmReadiness,
  recordAcknowledgement,
  downloadAcknowledgement,
  closeApplication,
  downloadPermitDocument,
  getFollowups,
  addFollowup,
  downloadFollowupDocument,
}
