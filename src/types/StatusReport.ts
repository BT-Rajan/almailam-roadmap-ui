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
  // Computed server-side against the Kuwait-time filing cutoff (see
  // status_report_service.py's filing_window_block_reason) -- lets the
  // portal show/disable the right thing before the engineer even opens
  // the form, rather than only rejecting on submit.
  canFileReport: boolean
  blockReason: string | null
}
