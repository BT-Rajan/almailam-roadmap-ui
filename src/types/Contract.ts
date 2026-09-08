export type ContractStatus = 'Draft' | 'Signed' | 'Active' | 'Expired' | 'Terminated'

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
  // undefined while an editable draft; set once finalized.
  finalizedAt?: string
  // Non-null while a signing code is outstanding -- lets the Contract
  // tab reopen the OTP dialog straight to "enter code" instead of
  // "send" when one's already on its way.
  otpSentAt?: string | null
  // Only set right after verify-otp -- false means the client's
  // signed-copy confirmation email failed to send, so the success
  // message shown to the signing user can say so honestly. Undefined
  // on every other response that carries a Contract.
  confirmationEmailSent?: boolean
}
