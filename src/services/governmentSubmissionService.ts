import { apiClient } from '@/services/httpClient'
import type { GovernmentSubmission } from '@/types/Submission'

/**
 * Fetch all government submissions from backend API
 */
async function getSubmissions(): Promise<GovernmentSubmission[]> {
  try {
    return await apiClient.get<GovernmentSubmission[]>('/api/government/submissions')
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
    return await apiClient.get<GovernmentSubmission[]>(`/api/projects/${projectId}/government-submissions`)
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
    return await apiClient.post<GovernmentSubmission>('/api/government/submissions', submissionData)
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
    return await apiClient.patch<GovernmentSubmission>(`/api/government/submissions/${submissionId}`, submissionData)
  } catch (error) {
    console.error(`Failed to update submission ${submissionId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update submission')
  }
}

/**
 * Delete a government submission via backend API
 */
async function deleteSubmission(submissionId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/government/submissions/${submissionId}`)
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
