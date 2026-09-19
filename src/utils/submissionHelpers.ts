import type { BadgeVariant } from '@/types/Ui'
import type { RequiredDocumentStatus, ResponseOutcome, SubmissionStage } from '@/types/Submission'

export const SUBMISSION_STAGES: SubmissionStage[] = ['Prepare', 'Apply', 'Track', 'Close']

const STAGE_VARIANTS: Record<SubmissionStage, BadgeVariant> = {
  Prepare: 'neutral',
  Apply: 'info',
  Track: 'warning',
  Close: 'success',
}

const OUTCOME_VARIANTS: Record<ResponseOutcome, BadgeVariant> = {
  Approved: 'success',
  Rejected: 'danger',
  'No Response': 'warning',
  Withdrawn: 'neutral',
}

const DOCUMENT_STATUS_VARIANTS: Record<RequiredDocumentStatus, BadgeVariant> = {
  Pending: 'neutral',
  Uploaded: 'info',
  Verified: 'success',
}

export function getSubmissionStageVariant(stage: SubmissionStage): BadgeVariant {
  return STAGE_VARIANTS[stage]
}

// A Close-stage application's badge should read by outcome rather than
// the generic "Close" label -- there's nothing to distinguish an
// Approved close from a Rejected/Withdrawn one otherwise.
export function getSubmissionOutcomeVariant(outcome: ResponseOutcome | null | undefined): BadgeVariant {
  return outcome ? OUTCOME_VARIANTS[outcome] : 'neutral'
}

export function getDocumentStatusVariant(status: RequiredDocumentStatus): BadgeVariant {
  return DOCUMENT_STATUS_VARIANTS[status]
}
