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
  status: 'Pending' | 'Completed' | 'Waived'
  completedAt: string | null
  completedByName: string | null
  waivedAt: string | null
  waivedByName: string | null
  waivedReason: string | null
}
