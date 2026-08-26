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
  // Set when this step was checked complete through the "were any
  // additional services rendered?" flow rather than as part of the
  // project's original quoted scope -- see ScopeExecutionPanel.vue.
  isAdditionalScope?: boolean
  contractCovered?: boolean | null
}

export interface ExecutionStepBulkItem {
  id: string
  completionPercentage: number
  remarks: string | null
  isExcluded: boolean
  excludedReason: string | null
}
