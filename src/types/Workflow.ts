export interface WorkflowStageConfig {
  id: string
  name: string
  description: string
}

export interface WorkflowTemplate {
  id: string
  name: string
  isDefault: boolean
  stages: WorkflowStageConfig[]
}
