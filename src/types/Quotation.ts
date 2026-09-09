export type QuotationStatus = 'Draft' | 'Approved' | 'Rejected' | 'Expired'

export interface QuotationLineItem {
  id: string
  description: string
  quantity: number
  unitPrice: number
}

export interface QuotationRevision {
  id: string
  revision: string
  date: string
  changedBy: string
  summary: string
}

/** One row from the quotation's audit trail (see backend
 * audit_service.get_history) -- document-lifecycle and status-change
 * events like "Quotation emailed"/"Quotation approved", not content
 * edits (those are QuotationRevision, above). Shown merged with
 * revisions in QuotationRevisionHistory.vue. */
export interface QuotationAuditEvent {
  id: string
  action: string
  user: string
  timestamp: string
  previousValue?: string
  newValue?: string
  reason?: string
}

export interface Quotation {
  id: string
  projectId: string
  quotationNo: string
  revision: string
  issueDate: string
  validity: string
  status: QuotationStatus
  currency: string
  preparedBy: string
  discountAmount: number
  notes: string
  termsAndConditions: string[]
  scopePhases: string[]
  paymentTerms: string[]
  lineItems: QuotationLineItem[]
  amount: number
  // undefined while an editable draft; set once finalized.
  finalizedAt?: string
  revisions: QuotationRevision[]
}
