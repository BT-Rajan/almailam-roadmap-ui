export type QuotationStatus = 'Draft' | 'Sent' | 'Approved' | 'Rejected' | 'Expired'

// The two pre-written, verbatim quotation letters staff can pick when
// creating a quotation. undefined/null keeps the original generic
// itemised-pricing layout for anything that doesn't use a letter.
export type QuotationTemplateKey = 'design-and-permits' | 'supervision'

export const QUOTATION_TEMPLATE_LABELS: Record<QuotationTemplateKey, string> = {
  'design-and-permits': 'Design & Permits Quotation (Arabic letter)',
  supervision: 'Supervision Quotation (Arabic letter)',
}

export type FeeFrequency = 'Lump Sum' | 'Monthly'

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
  taxRatePercent: number
  discountAmount: number
  notes: string
  termsAndConditions: string[]
  lineItems: QuotationLineItem[]
  amount: number
  // Lettered-template fields -- all optional/empty unless templateKey is set.
  templateKey?: QuotationTemplateKey
  clientRepresentative?: string
  subjectLine?: string
  projectReference?: string
  feeFrequency: FeeFrequency
  scopeItems: string[]
  paymentTerms: string[]
  // undefined while the letter is an editable draft; set once finalized.
  finalizedAt?: string
  revisions: QuotationRevision[]
}
