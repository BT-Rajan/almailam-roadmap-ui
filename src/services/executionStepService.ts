import { apiClient } from '@/services/httpClient'
import type { ExecutionStepTemplateItem, ProjectExecutionStep } from '@/types/ExecutionStep'

async function getTemplate(): Promise<ExecutionStepTemplateItem[]> {
  return apiClient.get<ExecutionStepTemplateItem[]>('/api/execution-step-template')
}

async function createTemplateStep(name: string, weightPercentage: number): Promise<ExecutionStepTemplateItem> {
  return apiClient.post<ExecutionStepTemplateItem>('/api/execution-step-template', { name, weightPercentage })
}

async function updateTemplateStep(
  stepId: string,
  fields: { name?: string; weightPercentage?: number },
): Promise<ExecutionStepTemplateItem> {
  return apiClient.patch<ExecutionStepTemplateItem>(`/api/execution-step-template/${stepId}`, fields)
}

async function deleteTemplateStep(stepId: string): Promise<void> {
  await apiClient.delete<void>(`/api/execution-step-template/${stepId}`)
}

async function moveTemplateStep(stepId: string, direction: 'up' | 'down'): Promise<ExecutionStepTemplateItem[]> {
  return apiClient.post<ExecutionStepTemplateItem[]>(`/api/execution-step-template/${stepId}/move`, { direction })
}

async function getProjectSteps(projectId: string): Promise<ProjectExecutionStep[]> {
  return apiClient.get<ProjectExecutionStep[]>(`/api/projects/${projectId}/execution-steps`)
}

async function completeStep(projectId: string, stepId: string): Promise<ProjectExecutionStep> {
  return apiClient.post<ProjectExecutionStep>(`/api/projects/${projectId}/execution-steps/${stepId}/complete`)
}

async function uncompleteStep(projectId: string, stepId: string): Promise<ProjectExecutionStep> {
  return apiClient.post<ProjectExecutionStep>(`/api/projects/${projectId}/execution-steps/${stepId}/uncomplete`)
}

export const executionStepService = {
  getTemplate,
  createTemplateStep,
  updateTemplateStep,
  deleteTemplateStep,
  moveTemplateStep,
  getProjectSteps,
  completeStep,
  uncompleteStep,
}
