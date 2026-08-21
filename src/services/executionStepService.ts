import { apiClient } from '@/services/httpClient'
import type { ExecutionStepTemplateItem, ProjectExecutionStep } from '@/types/ExecutionStep'

async function getTemplate(): Promise<ExecutionStepTemplateItem[]> {
  return apiClient.get<ExecutionStepTemplateItem[]>('/api/execution-step-template')
}

async function createTemplateStep(
  name: string,
  weightPercentage: number,
  stageKey: string,
  isOptional: boolean,
): Promise<ExecutionStepTemplateItem> {
  return apiClient.post<ExecutionStepTemplateItem>('/api/execution-step-template', {
    name,
    weightPercentage,
    stageKey,
    isOptional,
  })
}

async function updateTemplateStep(
  stepId: string,
  fields: { name?: string; weightPercentage?: number; stageKey?: string; isOptional?: boolean },
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

async function setStepProgress(
  projectId: string,
  stepId: string,
  completionPercentage: number,
  remarks: string | null,
): Promise<ProjectExecutionStep> {
  return apiClient.patch<ProjectExecutionStep>(`/api/projects/${projectId}/execution-steps/${stepId}/progress`, {
    completionPercentage,
    remarks,
  })
}

export const executionStepService = {
  getTemplate,
  createTemplateStep,
  updateTemplateStep,
  deleteTemplateStep,
  moveTemplateStep,
  getProjectSteps,
  setStepProgress,
}
