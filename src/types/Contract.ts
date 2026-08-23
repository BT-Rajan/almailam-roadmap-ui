export type ContractStatus = 'Draft' | 'Sent' | 'Signed' | 'Active' | 'Expired' | 'Terminated'

// The two pre-written, bilingual (Arabic-then-English) contract letters
// staff can pick when creating a contract. undefined/null keeps the
// original generic clause-list contract for anything not using a letter.
export type ContractTemplateKey = 'design-and-permits' | 'supervision'

export const CONTRACT_TEMPLATE_LABELS: Record<ContractTemplateKey, string> = {
  'design-and-permits': 'Design & Permits Contract (Bilingual: Arabic then English)',
  supervision: 'Supervision Contract (Bilingual: Arabic then English)',
}

export type ContractFeeFrequency = 'Lump Sum' | 'Monthly'

export interface ContractClause {
  id: string
  title: string
  content: string
}

export interface ContractRevision {
  id: string
  revision: string
  date: string
  changedBy: string
  summary: string
}

export interface Contract {
  id: string
  projectId: string
  // The quotation this contract was generated from -- every contract
  // created through the normal flow has one (see the workflow rule
  // that a contract requires an Approved, finalized quotation);
  // undefined only for contracts that predate that rule.
  quotationNo?: string
  contractNo: string
  templateName: string
  revision: string
  currency: string
  contractValue: number
  issueDate: string
  signedDate?: string
  expiryDate: string
  status: ContractStatus
  preparedBy: string
  clientRepresentative: string
  scopeSummary: string
  clauses: ContractClause[]
  revisions: ContractRevision[]
  // Lettered-template fields -- all empty/default unless templateKey is set.
  templateKey?: ContractTemplateKey
  isBilingual: boolean
  subjectLineAr?: string
  subjectLineEn?: string
  projectReference?: string
  feeFrequency: ContractFeeFrequency
  scopeItemsAr: string[]
  scopeItemsEn: string[]
  paymentTermsAr: string[]
  paymentTermsEn: string[]
  // undefined while the letter is an editable draft; set once finalized.
  finalizedAt?: string
}

export interface ContractAISummary {
  contractId: string
  summary: string
  details: string
  confidence: 'high' | 'medium' | 'low'
  suggestions: string[]
}
