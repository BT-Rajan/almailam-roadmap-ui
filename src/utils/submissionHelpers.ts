import type { BadgeVariant } from '@/types/Ui'
import type { RequiredDocumentStatus, SubmissionStatus } from '@/types/Submission'

export const SUBMISSION_STAGES: SubmissionStatus[] = [
  'Draft',
  'Submitted',
  'Under Review',
  'Comments Received',
  'Approved',
]

const STATUS_VARIANTS: Record<SubmissionStatus, BadgeVariant> = {
  Draft: 'neutral',
  Submitted: 'info',
  'Under Review': 'warning',
  'Comments Received': 'warning',
  Approved: 'success',
  Rejected: 'danger',
}

const DOCUMENT_STATUS_VARIANTS: Record<RequiredDocumentStatus, BadgeVariant> = {
  Pending: 'neutral',
  Uploaded: 'info',
  Verified: 'success',
}

export function getSubmissionStatusVariant(status: SubmissionStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getDocumentStatusVariant(status: RequiredDocumentStatus): BadgeVariant {
  return DOCUMENT_STATUS_VARIANTS[status]
}
