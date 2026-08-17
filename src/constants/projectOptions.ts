// Fixed reference list of engineering service types offered, used to
// populate the "Service" dropdown when creating a new project. Unlike
// the rest of what used to live in src/mock/, this isn't a stand-in for
// real backend data -- it's genuine static configuration.
export const PROJECT_SERVICES: string[] = [
  'Structural Engineering',
  'MEP Design',
  'Architectural Design',
  'Fire & Safety Engineering',
  'Civil Engineering',
]

// Mirrors backend/app/core/status_transitions.py's PROJECT_STAGE_ALLOWED_
// TRANSITIONS exactly -- kept in sync by hand, same as every other
// transition table in this app (see CLIENT_ONBOARDING_ALLOWED_TRANSITIONS
// for the established pattern). The backend is still the source of
// truth and re-validates independently; this only drives which options
// the UI offers.
export const PROJECT_STAGE_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Enquiry: ['Quotation'],
  Quotation: ['Contract'],
  Contract: ['Design'],
  Design: ['Government Submission'],
  'Government Submission': ['Review'],
  Review: ['Correction', 'Approval'],
  Correction: ['Review'],
  Approval: ['Completed'],
  Completed: ['Approval'],
}

// "Correction" always needs a reason. "Completed" -> "Approval" only
// needs one when reopening a completed project specifically -- not the
// normal "Review" -> "Approval" outcome, which shares the same target
// state, so this has to be a (from, to) check rather than a flat set of
// target states.
export function isStageReasonRequired(from: string, to: string): boolean {
  if (to === 'Correction') return true
  if (from === 'Completed' && to === 'Approval') return true
  return false
}

export const PROJECT_STATUS_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Active: ['On Hold', 'Completed', 'Cancelled'],
  'On Hold': ['Active', 'Cancelled'],
  Completed: ['Active'],
  Cancelled: ['Active'],
}

// "On Hold"/"Cancelled" always need one. "Completed"/"Cancelled" ->
// "Active" only needs one when reopening -- not the routine "On Hold"
// -> "Active" resume, which shares the same target state.
export function isStatusReasonRequired(from: string, to: string): boolean {
  if (to === 'On Hold' || to === 'Cancelled') return true
  if ((from === 'Completed' || from === 'Cancelled') && to === 'Active') return true
  return false
}
