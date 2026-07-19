import { WORKFLOW_TEMPLATES } from '@/mock/workflowTemplates'
import type { WorkflowTemplate } from '@/types/Workflow'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getTemplates(): Promise<WorkflowTemplate[]> {
  await simulateNetworkDelay()
  return WORKFLOW_TEMPLATES.map((template) => ({ ...template, stages: template.stages.map((stage) => ({ ...stage })) }))
}

export const workflowService = {
  getTemplates,
}
