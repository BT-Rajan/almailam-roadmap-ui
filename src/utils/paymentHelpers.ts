import type { BadgeVariant } from '@/types/Ui'
import type { AgreementStream, FinancialAgreement, FinancialSummary, ObligationStatus, PaymentObligation } from '@/types/Payment'

// Design/Permit work is billed once, split into up to 5 user-
// configurable installments (or paid in full as a single payment);
// Supervision is billed monthly and prorated automatically -- see
// generate_prorated_monthly_schedule. The AgreementStream key itself
// stays 'Design' (matches the DB enum and the service catalog's own
// branch name -- Permit is cataloged under the Design branch, migration
// 0060) -- only the label shown to staff reflects that it covers Permit
// fees too. Route every user-facing display of a stream through this,
// same convention as getWorkflowStageLabel (utils/projectHelpers.ts).
const AGREEMENT_STREAM_LABELS: Record<AgreementStream, string> = {
  Design: 'Design & Permit',
  Supervision: 'Supervision',
}

export function getAgreementStreamLabel(stream: AgreementStream): string {
  return AGREEMENT_STREAM_LABELS[stream]
}

function startOfDay(date: Date): number {
  const copy = new Date(date)
  copy.setHours(0, 0, 0, 0)
  return copy.getTime()
}

function todayTimestamp(): number {
  return startOfDay(new Date())
}

/**
 * Calculates the live status of a payment obligation from amountDue,
 * amountReceived, and dueDate vs. today — see Pass 19A section 5.
 * 'Cancelled' and 'Waived' are manual overrides and always win.
 */
export function computeObligationStatus(obligation: PaymentObligation, today: number = todayTimestamp()): ObligationStatus {
  if (obligation.manualStatus) return obligation.manualStatus

  const dueTimestamp = startOfDay(new Date(obligation.dueDate))
  const isPastDue = dueTimestamp < today
  const isDueToday = dueTimestamp === today
  const isFullyPaid = obligation.amountReceived >= obligation.amountDue
  const isPartiallyPaid = obligation.amountReceived > 0 && obligation.amountReceived < obligation.amountDue

  if (isFullyPaid) return 'Paid'
  if (isPartiallyPaid) return isPastDue ? 'Partially Overdue' : 'Partially Paid'
  if (isPastDue) return 'Overdue'
  if (isDueToday) return 'Due'
  return 'Scheduled'
}

export function getObligationAmountPending(obligation: PaymentObligation): number {
  return Math.max(0, obligation.amountDue - obligation.amountReceived)
}

function getObligationAmountOverdue(obligation: PaymentObligation, today: number = todayTimestamp()): number {
  const status = computeObligationStatus(obligation, today)
  if (status === 'Overdue' || status === 'Partially Overdue') return getObligationAmountPending(obligation)
  return 0
}

export function getObligationStatusVariant(status: ObligationStatus): BadgeVariant {
  const variants: Record<ObligationStatus, BadgeVariant> = {
    Scheduled: 'neutral',
    Due: 'warning',
    'Partially Paid': 'warning',
    Paid: 'success',
    Overdue: 'danger',
    'Partially Overdue': 'danger',
    Cancelled: 'neutral',
    Waived: 'info',
  }
  return variants[status]
}

/**
 * The next payment is the earliest (by sequence number) obligation that
 * is not fully settled and not cancelled/waived — see Pass 19A section 9.
 * An obligation further in the schedule must never be shown as "next"
 * while an earlier one remains unpaid.
 */
function getNextPaymentObligation(obligations: PaymentObligation[], today: number = todayTimestamp()): PaymentObligation | undefined {
  return [...obligations]
    .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    .find((obligation) => {
      const status = computeObligationStatus(obligation, today)
      return status !== 'Paid' && status !== 'Cancelled' && status !== 'Waived'
    })
}

function getDaysUntilDue(dueDate: string, today: number = todayTimestamp()): number {
  const dueTimestamp = startOfDay(new Date(dueDate))
  return Math.round((dueTimestamp - today) / 86_400_000)
}

/**
 * Aggregates a financial agreement's obligations into the summary shown
 * on the payment dashboard — see Pass 19A section 8 and 10.
 */
export function getFinancialSummary(agreement: FinancialAgreement, obligations: PaymentObligation[]): FinancialSummary {
  const today = todayTimestamp()
  const activeObligations = obligations.filter((obligation) => obligation.manualStatus !== 'Cancelled' && obligation.manualStatus !== 'Waived')

  const totalReceived = obligations.reduce((sum, obligation) => sum + obligation.amountReceived, 0)
  // Pending and overdue are mutually exclusive: once an obligation's due
  // date passes, its outstanding balance moves out of Total Pending and
  // into Total Overdue rather than being counted in both.
  const totalOverdue = activeObligations.reduce((sum, obligation) => sum + getObligationAmountOverdue(obligation, today), 0)
  const totalPending = activeObligations.reduce((sum, obligation) => {
    const status = computeObligationStatus(obligation, today)
    if (status === 'Overdue' || status === 'Partially Overdue') return sum
    return sum + getObligationAmountPending(obligation)
  }, 0)

  // A waived/cancelled obligation's un-received balance is money the
  // contract said was payable but that will never be collected --
  // excluded from Total Pending above, but still accounted for here so
  // Contract Value stays reconciled to Received + Pending + Overdue +
  // Waived + Cancelled instead of silently vanishing.
  const totalWaived = obligations.reduce((sum, obligation) => (obligation.manualStatus === 'Waived' ? sum + getObligationAmountPending(obligation) : sum), 0)
  const totalCancelled = obligations.reduce((sum, obligation) => (obligation.manualStatus === 'Cancelled' ? sum + getObligationAmountPending(obligation) : sum), 0)

  const nextPaymentObligation = getNextPaymentObligation(obligations, today)
  const nextPaymentDaysUntilDue = nextPaymentObligation ? getDaysUntilDue(nextPaymentObligation.dueDate, today) : undefined
  const nextPaymentIsOverdue = nextPaymentObligation ? nextPaymentDaysUntilDue !== undefined && nextPaymentDaysUntilDue < 0 : false

  // Should normally be zero -- nonzero only means an Adjustment has moved
  // obligation amounts without a matching change to contractAmount, so
  // the schedule and the contract have drifted apart. Surfaced rather
  // than silently absorbed either way.
  const scheduleVariance = agreement.contractAmount - (totalReceived + totalPending + totalOverdue + totalWaived + totalCancelled)

  return {
    contractAmount: agreement.contractAmount,
    // Filled in by the caller when it has quotation data on hand (see
    // paymentStore.summaryForAgreement) -- this pure function only ever
    // sees the agreement/obligations, never the quotation itself.
    estimateAmount: null,
    totalReceived,
    totalPending,
    totalOverdue,
    totalWaived,
    totalCancelled,
    scheduleVariance,
    nextPaymentObligation,
    nextPaymentDaysUntilDue,
    nextPaymentIsOverdue,
  }
}
