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
  // Non-null while an approval code is outstanding -- lets the
  // Quotation tab reopen the OTP dialog straight to "enter code"
  // instead of "send" when one's already on its way.
  otpSentAt?: string | null
  revisions: QuotationRevision[]
}
