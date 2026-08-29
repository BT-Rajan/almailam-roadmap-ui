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
// stage hop. "Execution & Tracking" and "Completed" were removed
// entirely -- "Government Submission" is now the terminal stage.
// "Supervision" sits alongside "Design" -- a project can include
// either, both, or neither (Project.includesDesign/includesSupervision),
// so this is deliberately the permissive superset of every structurally
// possible edge, same as the backend's own table; whether "Design"/
// "Supervision" specifically applies to a given project is enforced
// server-side, not by which options this offers. See
// backend/app/core/status_transitions.py's own comment.
export const PROJECT_STAGE_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Requirement: ['Quotation'],
  Quotation: ['Contract'],
  Contract: ['Design', 'Supervision', 'Government Submission'],
  Design: ['Supervision', 'Government Submission'],
  Supervision: ['Government Submission'],
  // The reopening paths backward -- an authority's feedback during
  // Government Submission can require design or supervision changes.
  // Requires a reason (see isStageReasonRequired below), unlike the
  // normal forward flow.
  'Government Submission': ['Design', 'Supervision'],
}

// "Government Submission" -> "Design"/"Supervision" is a correction (an
// authority's feedback requiring changes), not the normal forward flow
// that also targets those same stages (from "Contract"/"Design"), so
// this has to be a (from, to) check rather than a flat set of target
// states.
export function isStageReasonRequired(from: string, to: string): boolean {
  if (from === 'Government Submission' && (to === 'Design' || to === 'Supervision')) return true
  return false
}

// No "Completed" value -- a project never reaches a terminal "done"
// status, only Active/On Hold/Cancelled.
export const PROJECT_STATUS_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Active: ['On Hold', 'Cancelled'],
  'On Hold': ['Active', 'Cancelled'],
  Cancelled: ['Active'],
}

// "On Hold"/"Cancelled" always need one. "Cancelled" -> "Active" only
// needs one when reopening -- not the routine "On Hold" -> "Active"
// resume, which shares the same target state.
export function isStatusReasonRequired(from: string, to: string): boolean {
  if (to === 'On Hold' || to === 'Cancelled') return true
  if (from === 'Cancelled' && to === 'Active') return true
  return false
}
