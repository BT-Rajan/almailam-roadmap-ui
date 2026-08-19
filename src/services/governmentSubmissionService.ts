import { apiClient } from '@/services/httpClient'
import type { GovernmentSubmission, SubmissionStatus } from '@/types/Submission'

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

export const governmentSubmissionService = {
  getSubmissions,
  getSubmissionsByProject,
  createSubmission,
  updateSubmission,
  setSubmissionStatus,
}
