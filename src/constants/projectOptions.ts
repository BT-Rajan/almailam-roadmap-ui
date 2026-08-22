// Formerly the fixed reference list of engineering service types offered.
// Superseded by the admin-configurable Service Catalog (Administration >
// Service Catalog, see stores/serviceCatalogStore.ts) -- the "Service"
// dropdown on project creation/edit now reads from there instead, so any
// number of services can be added or removed without a code change. Kept
// here, unused, only as the default seed list the backend falls back to
// on a fresh install (see backend/app/services/service_catalog_service.py
// DEFAULT_SERVICE_NAMES) -- update both together if the defaults change.
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
// "Correction" used to be its own stage here (Review <-> Correction).
// Merged into a single "Review" stage -- a correction cycle during
// review is logged as a note on the project instead of a separate
// stage hop. "Review" was itself renamed to "Execution & Tracking" and
// "Approval" dropped entirely. See backend/app/core/status_transitions
// .py's own comment.
export const PROJECT_STAGE_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Enquiry: ['Quotation'],
  Quotation: ['Contract'],
  Contract: ['Design'],
  Design: ['Government Submission'],
  'Government Submission': ['Execution & Tracking'],
  'Execution & Tracking': ['Completed'],
  Completed: ['Execution & Tracking'],
}

// "Completed" -> "Execution & Tracking" only needs a reason when
// reopening a completed project specifically -- not the normal
// "Execution & Tracking" -> "Completed" outcome, which shares the same
// target state, so this has to be a (from, to) check rather than a
// flat set of target states.
export function isStageReasonRequired(from: string, to: string): boolean {
  if (from === 'Completed' && to === 'Execution & Tracking') return true
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
