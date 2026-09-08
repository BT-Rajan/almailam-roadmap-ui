// Mirrors backend/app/core/status_transitions.py's QUOTATION_ALLOWED_
// TRANSITIONS and CONTRACT_ALLOWED_TRANSITIONS -- kept in sync by hand,
// same as PROJECT_STAGE_ALLOWED_TRANSITIONS in constants/
// projectOptions.ts. The backend is still the source of truth and
// re-validates independently; this only drives which options the UI
// offers.
//
// Both quotations and contracts share one extra rule the backend
// enforces that isn't a transition-table entry: a document can't move
// out of Draft status until it's been saved as Final (finalized_at
// set). See ProjectQuotationTab.vue / ProjectContractTab.vue, which
// only offer "Change Status" once that's true.
//
// "Approved" is deliberately NOT offered here as a manual "Change
// Status" target even though the backend's own table allows it --
// quotation_service.set_status still accepts it (that's what
// confirm_quotation_approval calls), but the only way to actually
// reach it is a confirmed signed-document upload (see
// ProjectQuotationTab.vue's SignedDocumentUploadDialog), same
// treatment as Client's "Ready" and the Requirement stage's own scope
// confirmation.
export const QUOTATION_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Draft: ['Rejected', 'Expired'],
  Approved: [],
  Rejected: ['Draft'],
  Expired: ['Draft'],
}

export const QUOTATION_STATUSES_REQUIRING_REASON = new Set(['Rejected'])

export function isQuotationReasonRequired(newStatus: string): boolean {
  return QUOTATION_STATUSES_REQUIRING_REASON.has(newStatus)
}

// "Signed" is deliberately NOT offered here as a manual "Change Status"
// target even though the backend's own table allows it --
// contract_service.set_status still accepts it (that's what
// confirm_contract_signing calls), but the only way to actually reach
// it is a confirmed signed-document upload (see ProjectContractTab.vue's
// SignedDocumentUploadDialog), same treatment as Quotation's "Approved".
export const CONTRACT_ALLOWED_TRANSITIONS: Record<string, string[]> = {
  Draft: [],
  Signed: ['Active'],
  Active: ['Expired', 'Terminated'],
  Expired: ['Draft'],
  Terminated: [],
}

export const CONTRACT_STATUSES_REQUIRING_REASON = new Set(['Terminated'])

export function isContractReasonRequired(newStatus: string): boolean {
  return CONTRACT_STATUSES_REQUIRING_REASON.has(newStatus)
}
