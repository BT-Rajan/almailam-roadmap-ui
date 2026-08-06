import { apiClient } from '@/services/httpClient'
import type { WorkflowStageConfig, WorkflowTemplate } from '@/types/Workflow'

/**
 * Fetch all workflow templates from backend API
 */
async function getTemplates(): Promise<WorkflowTemplate[]> {
  try {
    return await apiClient.get<WorkflowTemplate[]>('/api/workflows/templates')
  } catch (error) {
    console.error('Failed to fetch workflow templates:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch templates')
  }
}

/**
 * Add a new stage to a workflow template via backend API
 */
async function addStage(templateId: string, name: string, description: string): Promise<WorkflowStageConfig> {
  try {
    return await apiClient.post<WorkflowStageConfig>(`/api/workflows/templates/${templateId}/stages`, {
      name,
      description,
    })
  } catch (error) {
    console.error('Failed to add workflow stage:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add stage')
  }
}

/**
 * Update a workflow stage's name and/or description via backend API
 */
async function updateStage(
  stageId: string,
  fields: Partial<Pick<WorkflowStageConfig, 'name' | 'description'>>,
): Promise<WorkflowStageConfig> {
  try {
    return await apiClient.patch<WorkflowStageConfig>(`/api/workflows/stages/${stageId}`, fields)
  } catch (error) {
    console.error(`Failed to update stage ${stageId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update stage')
  }
}

/**
 * Remove a stage from a workflow template via backend API
 */
async function removeStage(stageId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/workflows/stages/${stageId}`)
  } catch (error) {
    console.error(`Failed to remove stage ${stageId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove stage')
  }
}

/**
 * Move a stage up or down within its template via backend API. Returns the
 * template's full, re-sequenced stage list.
 */
async function moveStage(stageId: string, direction: 'up' | 'down'): Promise<WorkflowStageConfig[]> {
  try {
    return await apiClient.post<WorkflowStageConfig[]>(`/api/workflows/stages/${stageId}/move`, { direction })
  } catch (error) {
    console.error(`Failed to move stage ${stageId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to move stage')
  }
}

/**
 * Mark a workflow template as the default via backend API. Returns every
 * template so the caller can refresh isDefault flags across the board.
 */
async function setDefaultTemplate(templateId: string): Promise<WorkflowTemplate[]> {
  try {
    return await apiClient.post<WorkflowTemplate[]>(`/api/workflows/templates/${templateId}/set-default`)
  } catch (error) {
    console.error(`Failed to set default template ${templateId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to set default template')
  }
}

export const workflowService = {
  getTemplates,
  addStage,
  updateStage,
  removeStage,
  moveStage,
  setDefaultTemplate,
}
