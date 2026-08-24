// Mirrors backend/app/core/status_transitions.py's QUOTATION_ALLOWED_
// TRANSITIONS and CONTRACT_ALLOWED_TRANSITIONS exactly -- kept in sync
// by hand, same as PROJECT_STAGE_ALLOWED_TRANSITIONS in
// constants/projectOptions.ts. The backend is still the source of
// truth and re-validates independently; this only drives which
// options the UI offers.
//
// Both quotations and contracts share one extra rule the backend
// enforces that isn't a transition-table entry: a document can't move
// out of Draft status until it's been saved as Final (finalized_at
// set). See ProjectQuotationTab.vue / ProjectContractTab.vue, which
// only offer "Change Status" once that's true.
export const QUOTATION_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Draft: ['Sent'],
  Sent: ['Approved', 'Rejected', 'Expired'],
  Approved: [],
  Rejected: ['Draft'],
  Expired: ['Draft'],
}

export const QUOTATION_STATUSES_REQUIRING_REASON = new Set(['Rejected'])

export function isQuotationReasonRequired(newStatus: string): boolean {
  return QUOTATION_STATUSES_REQUIRING_REASON.has(newStatus)
}

export const CONTRACT_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Draft: ['Sent'],
  Sent: ['Signed', 'Draft'],
  Signed: ['Active'],
  Active: ['Expired', 'Terminated'],
  Expired: ['Draft'],
  Terminated: [],
}

export const CONTRACT_STATUSES_REQUIRING_REASON = new Set(['Terminated'])

export function isContractReasonRequired(newStatus: string): boolean {
  return CONTRACT_STATUSES_REQUIRING_REASON.has(newStatus)
}
