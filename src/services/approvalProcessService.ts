import { apiClient } from '@/services/httpClient'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'

async function getProjectSteps(projectId: string): Promise<ProjectApprovalStep[]> {
  return apiClient.get<ProjectApprovalStep[]>(`/api/projects/${projectId}/approval-steps`)
}

async function completeStep(projectId: string, stepId: string): Promise<ProjectApprovalStep> {
  return apiClient.post<ProjectApprovalStep>(`/api/projects/${projectId}/approval-steps/${stepId}/complete`)
}

async function uncompleteStep(projectId: string, stepId: string): Promise<ProjectApprovalStep> {
  return apiClient.post<ProjectApprovalStep>(`/api/projects/${projectId}/approval-steps/${stepId}/uncomplete`)
}

async function waiveStep(projectId: string, stepId: string, reason: string): Promise<ProjectApprovalStep> {
  return apiClient.post<ProjectApprovalStep>(`/api/projects/${projectId}/approval-steps/${stepId}/waive`, { reason })
}

async function unwaiveStep(projectId: string, stepId: string): Promise<ProjectApprovalStep> {
  return apiClient.post<ProjectApprovalStep>(`/api/projects/${projectId}/approval-steps/${stepId}/unwaive`)
}

export const approvalProcessService = { getProjectSteps, completeStep, uncompleteStep, waiveStep, unwaiveStep }
