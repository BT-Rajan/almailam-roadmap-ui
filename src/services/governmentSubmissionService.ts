import { apiClient } from '@/services/httpClient'
import type { GovernmentSubmission } from '@/types/Submission'

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

/**
 * Create a new government submission via backend API
 */
async function createSubmission(submissionData: Partial<GovernmentSubmission>): Promise<GovernmentSubmission> {
  try {
    return await apiClient.post<GovernmentSubmission>('/api/submissions', submissionData)
  } catch (error) {
    console.error('Failed to create submission:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create submission')
  }
}

/**
 * Update a government submission via backend API
 */
async function updateSubmission(submissionId: string, submissionData: Partial<GovernmentSubmission>): Promise<GovernmentSubmission> {
  try {
    return await apiClient.patch<GovernmentSubmission>(`/api/submissions/${submissionId}`, submissionData)
  } catch (error) {
    console.error(`Failed to update submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update submission')
  }
}

/**
 * Delete a government submission via backend API
 *
 * NOTE: the backend does not expose a delete endpoint for submissions (by
 * design -- submissions are an audited government-facing record, so they're
 * cancelled/withdrawn via a status change rather than removed). This
 * function is currently unused; calling it will 404 until/unless a real
 * withdrawal workflow is built.
 */
async function deleteSubmission(submissionId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/submissions/${submissionId}`)
  } catch (error) {
    console.error(`Failed to delete submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete submission')
  }
}

export const governmentSubmissionService = {
  getSubmissions,
  getSubmissionsByProject,
  createSubmission,
  updateSubmission,
  deleteSubmission,
}
