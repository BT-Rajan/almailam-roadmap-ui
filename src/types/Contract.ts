export type ContractStatus = 'Draft' | 'Sent' | 'Signed' | 'Active' | 'Expired' | 'Terminated'

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
}

export interface ContractAISummary {
  contractId: string
  summary: string
  details: string
  confidence: 'high' | 'medium' | 'low'
  suggestions: string[]
}
