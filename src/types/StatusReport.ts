export type StatusReportSupervisionType = 'Full-time' | 'Part-time'
export type StatusReportStatus = 'Pending' | 'Attached'

export interface StatusReportImage {
  id: string
  filename: string
  sizeBytes: number
  createdAt: string
}

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
  // Up to MAX_REPORT_IMAGES (5) -- each stamped server-side with the
  // filing engineer's name, project number, and date/time before being
  // saved (see backend status_report_service.stamp_report_image).
  images: StatusReportImage[]
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
