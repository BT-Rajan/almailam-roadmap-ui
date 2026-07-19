export type QuotationStatus = 'Draft' | 'Sent' | 'Approved' | 'Rejected' | 'Expired'

export interface QuotationLineItem {
  id: string
  description: string
  quantity: number
  unitPrice: number
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
}
