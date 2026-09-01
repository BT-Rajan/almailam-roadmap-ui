export type PaymentMode = 'Cash' | 'Bank Transfer' | 'Credit Card' | 'Debit Card' | 'Online Payment' | 'Cheque' | 'Other'

export type PaymentFrequency = 'One-time' | 'Daily' | 'Weekly' | 'Monthly' | 'Quarterly' | 'Half-yearly' | 'Yearly' | 'Custom'

// 'Cancelled' and 'Waived' are manual overrides set by an authorised
// action and are stored as-is. Every other status is recalculated from
// amountDue / amountReceived / dueDate — see utils/paymentHelpers.ts.
export type ObligationStatus = 'Scheduled' | 'Due' | 'Partially Paid' | 'Paid' | 'Overdue' | 'Partially Overdue' | 'Cancelled' | 'Waived'

export type FinancialEventType =
  | 'Agreement Created'
  | 'Obligation Created'
  | 'Payment Received'
  | 'Payment Allocated'
  | 'Payment Refunded'
  | 'Obligation Cancelled'
  | 'Obligation Waived'
  | 'Adjustment Applied'

// Which billing stream this agreement covers (migration 0059) -- a project
// can have one Design (one-time) agreement and one Supervision (monthly,
// day-prorated) agreement side by side.
export type AgreementStream = 'Design' | 'Supervision'

export interface FinancialAgreement {
  id: string
  projectId: string
  stream: AgreementStream
  contractAmount: number
  currency: string
  contractStartDate: string
  contractEndDate?: string
  agreementDate: string
  quotationReference?: string
  contractReference?: string
  paymentMode: PaymentMode
  paymentFrequency: PaymentFrequency
}

export interface PaymentObligation {
  id: string
  agreementId: string
  sequenceNumber: number
  description: string
  amountDue: number
  dueDate: string
  amountReceived: number
  // Manual override only — 'Cancelled' or 'Waived'. Anything else here
  // is ignored in favour of the live calculation.
  manualStatus?: 'Cancelled' | 'Waived'
  datePaid?: string
  paymentMethod?: PaymentMode
  referenceNumber?: string
  notes?: string
}

export interface Payment {
  id: string
  agreementId: string
  projectId: string
  amountReceived: number
  paymentDate: string
  paymentMode: PaymentMode
  referenceNumber?: string
  payer: string
  receivingAccount?: string
  notes?: string
  createdBy: string
  createdDate: string
}

export interface PaymentAllocation {
  id: string
  paymentId: string
  obligationId: string
  amountAllocated: number
}

export interface FinancialAuditEvent {
  id: string
  agreementId: string
  action: FinancialEventType
  user: string
  timestamp: string
  previousValue?: string
  newValue?: string
  reason?: string
}

export interface Refund {
  id: string
  paymentId: string
  agreementId: string
  refundAmount: number
  refundDate: string
  reason: string
  authorisingUser: string
  reference?: string
}

export type AdjustmentType = 'Increase' | 'Decrease' | 'Correction'

export interface Adjustment {
  id: string
  agreementId: string
  type: AdjustmentType
  amount: number
  reason: string
  authorisingUser: string
  date: string
}

export interface FinancialSummary {
  contractAmount: number
  // The originating quotation's amount, when the agreement was created
  // from one -- null when there's no linked quotation.
  estimateAmount: number | null
  totalReceived: number
  totalPending: number
  totalOverdue: number
  totalWaived: number
  totalCancelled: number
  scheduleVariance: number
  nextPaymentObligation?: PaymentObligation
  nextPaymentDaysUntilDue?: number
  nextPaymentIsOverdue: boolean
}

export interface RecordPaymentAllocationInput {
  obligationId: string
  amount: number
}

export interface RecordPaymentInput {
  agreementId: string
  projectId: string
  amountReceived: number
  paymentDate: string
  paymentMode: PaymentMode
  referenceNumber?: string
  payer: string
  notes?: string
  allocations: RecordPaymentAllocationInput[]
}

export interface CreateAgreementInput {
  projectId: string
  stream: AgreementStream
  // Required for a Design agreement (unchanged from before); ignored for
  // Supervision -- the backend derives all of these from the project's
  // selected Supervision activities via generate_prorated_monthly_schedule.
  contractAmount?: number
  currency: string
  contractStartDate?: string
  contractEndDate?: string
  agreementDate: string
  quotationReference?: string
  contractReference?: string
  paymentMode: PaymentMode
  paymentFrequency?: PaymentFrequency
}
