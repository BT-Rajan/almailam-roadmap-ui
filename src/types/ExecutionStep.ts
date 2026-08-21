export interface ExecutionStepTemplateItem {
  id: string
  name: string
  sequenceNumber: number
  weightPercentage: number
  stageKey: string
  isOptional: boolean
}

export interface ProjectExecutionStep {
  id: string
  name: string
  sequenceNumber: number
  weightPercentage: number
  stageKey: string
  isOptional: boolean
  completionPercentage: number
  remarks: string | null
}
