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
// entirely. "Payment Plan" sits between Quotation and Contract -- the
// project's financial agreement(s) have to be generated and approved
// before a contract is even drafted.
//
// Design, Government Submission (Permits, "Approvals & Permits"), and
// Supervision run in PARALLEL off Contract, not sequentially -- a
// project includes any combination of the three, or none
// (Project.includesDesign/includesGovernmentSubmission/
// includesSupervision), so this is deliberately the permissive
// superset of every structurally possible edge, same as the backend's
// own table; whether each specifically applies to a given project is
// enforced server-side, not by which options this offers. Each of the
// three can move freely to either of the other two (a lateral "which
// track is focused" pointer, not a real gate), and all three lead to
// "Handover", the real terminal stage.
export const PROJECT_STAGE_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Requirement: ['Quotation'],
  Quotation: ['Payment Plan'],
  'Payment Plan': ['Contract'],
  Contract: ['Design', 'Government Submission', 'Supervision'],
  Design: ['Government Submission', 'Supervision', 'Handover'],
  'Government Submission': ['Design', 'Supervision', 'Handover'],
  Supervision: ['Design', 'Government Submission', 'Handover'],
  // The one reopening path out of Handover -- back to any of the three
  // parallel tracks, in case something turns up after convergence that
  // needs redoing.
  Handover: ['Design', 'Government Submission', 'Supervision'],
}

// Reopening one of the three parallel tracks after Handover is a
// correction -- can't live in a flat set of target states, since Design/
// Government Submission/Supervision are also each other's normal,
// reason-free lateral targets and a flat set can't tell "from Handover"
// apart from "from a peer track".
export function isStageReasonRequired(from: string, to: string): boolean {
  const parallelTracks = ['Design', 'Government Submission', 'Supervision']
  return from === 'Handover' && parallelTracks.includes(to)
}

// "Completed" is a real terminal status now, but it's never a manual
// pick from this dialog -- a project only reaches it by the client
// confirming a signed hand-over acknowledgment upload (see
// try_complete_project/confirm_project_handover in project_service.py),
// so it's deliberately left out of Active's manual targets here even
// though the backend's own PROJECT_STATUS_ALLOWED_TRANSITIONS allows Active -> Completed
// for that system-driven transition. Completed itself has no further
// transitions, matching the backend.
export const PROJECT_STATUS_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Active: ['On Hold', 'Cancelled'],
  'On Hold': ['Active', 'Cancelled'],
  Cancelled: ['Active'],
  Completed: [],
}

// "On Hold"/"Cancelled" always need one. "Cancelled" -> "Active" only
// needs one when reopening -- not the routine "On Hold" -> "Active"
// resume, which shares the same target state.
export function isStatusReasonRequired(from: string, to: string): boolean {
  if (to === 'On Hold' || to === 'Cancelled') return true
  if (from === 'Cancelled' && to === 'Active') return true
  return false
}
