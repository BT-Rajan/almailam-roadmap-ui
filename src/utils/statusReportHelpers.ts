import type { StatusReportStatus } from '@/types/StatusReport'
import type { BadgeVariant } from '@/types/Ui'

/**
 * "Pending" / "Attached" are the *recipient's* review-queue states
 * (see status_report_service.py) -- correct for the Status Report
 * Inbox, where "Pending" genuinely means "waiting on you to review
 * this". Shown to the *filing engineer* on the Site Engineer Portal,
 * though, "Pending" reads as if their own filing is unfinished or
 * stuck, when the report has in fact already gone in successfully.
 * These map the same underlying status to the engineer's-eye-view
 * label instead, without touching the stored value or the recipient
 * side's wording.
 */
export function engineerStatusLabel(status: StatusReportStatus): string {
  if (status === 'Pending') return 'Submitted'
  return 'Reviewed'
}

export function engineerStatusVariant(status: StatusReportStatus): BadgeVariant {
  if (status === 'Pending') return 'info'
  return 'success'
}
