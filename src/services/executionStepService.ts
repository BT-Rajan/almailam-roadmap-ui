import { apiClient } from '@/services/httpClient'
import type {
  ExecutionStepBulkItem,
  ExecutionStepSet,
  ExecutionStepTemplateItem,
  ProjectExecutionStep,
} from '@/types/ExecutionStep'

async function getStepSets(): Promise<ExecutionStepSet[]> {
  return apiClient.get<ExecutionStepSet[]>('/api/execution-step-sets')
}

async function createStepSet(name: string, description: string | null): Promise<ExecutionStepSet> {
  return apiClient.post<ExecutionStepSet>('/api/execution-step-sets', { name, description })
}

async function updateStepSet(
  stepSetId: string,
  fields: { name?: string; description?: string | null },
): Promise<ExecutionStepSet> {
  return apiClient.patch<ExecutionStepSet>(`/api/execution-step-sets/${stepSetId}`, fields)
}

async function deleteStepSet(stepSetId: string): Promise<void> {
  await apiClient.delete<void>(`/api/execution-step-sets/${stepSetId}`)
}

async function getTemplate(stepSetId: string): Promise<ExecutionStepTemplateItem[]> {
  return apiClient.get<ExecutionStepTemplateItem[]>(`/api/execution-step-sets/${stepSetId}/steps`)
}

async function createTemplateStep(
  stepSetId: string,
  name: string,
  weightPercentage: number,
  stageKey: string,
  isOptional: boolean,
  triggerKey: string,
): Promise<ExecutionStepTemplateItem> {
  return apiClient.post<ExecutionStepTemplateItem>(`/api/execution-step-sets/${stepSetId}/steps`, {
    name,
    weightPercentage,
    stageKey,
    isOptional,
    triggerKey,
  })
}

async function updateTemplateStep(
  stepId: string,
  fields: { name?: string; weightPercentage?: number; stageKey?: string; isOptional?: boolean; triggerKey?: string },
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

async function addCustomProjectStep(
  projectId: string,
  name: string,
  weightPercentage: number,
  stageKey: string,
): Promise<ProjectExecutionStep> {
  return apiClient.post<ProjectExecutionStep>(`/api/projects/${projectId}/execution-steps`, {
    name,
    weightPercentage,
    stageKey,
  })
}

async function deleteCustomProjectStep(projectId: string, stepId: string): Promise<void> {
  await apiClient.delete<void>(`/api/projects/${projectId}/execution-steps/${stepId}`)
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

async function bulkSaveProjectSteps(
  projectId: string,
  steps: ExecutionStepBulkItem[],
): Promise<ProjectExecutionStep[]> {
  return apiClient.patch<ProjectExecutionStep[]>(`/api/projects/${projectId}/execution-steps`, { steps })
}

export const executionStepService = {
  getStepSets,
  createStepSet,
  updateStepSet,
  deleteStepSet,
  getTemplate,
  createTemplateStep,
  updateTemplateStep,
  deleteTemplateStep,
  moveTemplateStep,
  getProjectSteps,
  addCustomProjectStep,
  deleteCustomProjectStep,
  setStepProgress,
  bulkSaveProjectSteps,
}
