import { apiClient } from '@/services/httpClient'
import type { WorkflowTemplate } from '@/types/Workflow'

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
 * Get a specific workflow template by ID from backend API
 */
async function getTemplateById(templateId: string): Promise<WorkflowTemplate | undefined> {
  try {
    return await apiClient.get<WorkflowTemplate>(`/api/workflows/templates/${templateId}`)
  } catch (error) {
    console.error(`Failed to fetch template ${templateId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch template')
  }
}

/**
 * Create a new workflow instance via backend API
 */
async function createWorkflow(templateId: string, entityType: string, entityId: string): Promise<any> {
  try {
    return await apiClient.post('/api/workflows', {
      template_id: templateId,
      entity_type: entityType,
      entity_id: entityId,
    })
  } catch (error) {
    console.error('Failed to create workflow:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create workflow')
  }
}

/**
 * Advance workflow to next stage via backend API
 */
async function advanceStage(workflowId: string): Promise<any> {
  try {
    return await apiClient.post(`/api/workflows/${workflowId}/advance-stage`, {})
  } catch (error) {
    console.error('Failed to advance workflow stage:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to advance stage')
  }
}

export const workflowService = {
  getTemplates,
  getTemplateById,
  createWorkflow,
  advanceStage,
}
