import { GOVERNMENT_SUBMISSIONS } from '@/mock/governmentSubmissions'
import type { GovernmentSubmission } from '@/types/Submission'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getSubmissions(): Promise<GovernmentSubmission[]> {
  await simulateNetworkDelay()
  return [...GOVERNMENT_SUBMISSIONS]
}

async function getSubmissionsByProject(projectId: string): Promise<GovernmentSubmission[]> {
  await simulateNetworkDelay()
  return GOVERNMENT_SUBMISSIONS.filter((submission) => submission.projectId === projectId)
}

export const governmentSubmissionService = {
  getSubmissions,
  getSubmissionsByProject,
}
