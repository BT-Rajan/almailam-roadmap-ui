export interface ExecutionStepTemplateItem {
  id: string
  name: string
  sequenceNumber: number
  weightPercentage: number
}

export interface ProjectExecutionStep {
  id: string
  name: string
  sequenceNumber: number
  weightPercentage: number
  status: 'Pending' | 'Completed'
  completedAt: string | null
  completedByName: string | null
}
