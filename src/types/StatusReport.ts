export type StatusReportSupervisionType = 'Full-time' | 'Part-time'
export type StatusReportStatus = 'Pending' | 'Attached'

export interface StatusReport {
  id: string
  reportNo: string
  projectId: string
  projectName: string
  engineerId: string
  engineerName: string
  reportDate: string
  receiptType: string | null
  supervisionType: StatusReportSupervisionType
  notes: string
  status: StatusReportStatus
  attachedTaskId: string | null
  attachedBy: string | null
  attachedAt: string | null
  createdAt: string
}

export interface EngineerProjectOption {
  id: string
  projectName: string
}
