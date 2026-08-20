export interface ProjectApprovalStep {
  id: string
  name: string
  sequenceNumber: number
  status: 'Pending' | 'Completed'
  completedAt: string | null
  completedByName: string | null
}
