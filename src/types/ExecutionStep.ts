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
  isExcluded: boolean
  excludedReason: string | null
  completionPercentage: number
  remarks: string | null
}

export interface ExecutionStepBulkItem {
  id: string
  completionPercentage: number
  remarks: string | null
  isExcluded: boolean
  excludedReason: string | null
}
