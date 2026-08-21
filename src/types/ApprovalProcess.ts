export interface ProjectApprovalStep {
  id: string
  name: string
  stageKey: string
  sequenceNumber: number
  isOptional: boolean
  status: 'Pending' | 'Completed' | 'Waived'
  completedAt: string | null
  completedByName: string | null
  waivedAt: string | null
  waivedByName: string | null
  waivedReason: string | null
}
