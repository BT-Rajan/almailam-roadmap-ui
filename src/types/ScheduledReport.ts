export type ScheduledReportType = 'business_summary' | 'financial_summary' | 'project_status'
export type ScheduledReportPeriod = 'last_7_days' | 'last_30_days' | 'this_month' | 'last_month' | 'this_quarter' | 'this_year'
export type ScheduledReportFrequency = 'once' | 'daily' | 'weekly' | 'monthly'
export type ScheduledReportRunStatus = 'sent' | 'failed'

export interface ScheduledReport {
  id: string
  name: string
  reportType: ScheduledReportType
  projectNo: string | null
  period: ScheduledReportPeriod | null
  recipients: string[]
  subject: string | null
  messageBody: string | null
  frequency: ScheduledReportFrequency
  // "HH:MM", local to CompanySettings.timezone.
  sendTime: string | null
  // ISO datetime -- only for frequency='once'.
  sendDatetime: string | null
  // 0=Monday..6=Sunday -- only for frequency='weekly'.
  dayOfWeek: number | null
  // 1..31 -- only for frequency='monthly'.
  dayOfMonth: number | null
  startDate: string | null
  // null = no end date ("infinite") -- the schedule keeps firing until turned off.
  endDate: string | null
  isActive: boolean
  nextRunAt: string | null
  lastRunAt: string | null
  lastRunStatus: ScheduledReportRunStatus | null
  lastRunError: string | null
  createdBy: string
  createdAt: string
  updatedAt: string
}

// Same shape sent for both create (POST) and update (PATCH) -- the
// backend's ScheduledReportIn always represents the schedule's full
// configuration, matching how the admin form always submits the whole
// thing rather than a partial diff.
export interface ScheduledReportInput {
  name: string
  reportType: ScheduledReportType
  projectNo: string | null
  period: ScheduledReportPeriod | null
  recipients: string[]
  subject: string | null
  messageBody: string | null
  frequency: ScheduledReportFrequency
  sendTime: string | null
  sendDatetime: string | null
  dayOfWeek: number | null
  dayOfMonth: number | null
  startDate: string | null
  endDate: string | null
  isActive: boolean
}
