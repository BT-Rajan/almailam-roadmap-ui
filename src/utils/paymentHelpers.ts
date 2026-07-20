import type { BadgeVariant } from '@/types/Ui'
import type { FinancialAgreement, FinancialSummary, ObligationStatus, PaymentObligation } from '@/types/Payment'

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

export function getObligationAmountOverdue(obligation: PaymentObligation, today: number = todayTimestamp()): number {
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
export function getNextPaymentObligation(obligations: PaymentObligation[], today: number = todayTimestamp()): PaymentObligation | undefined {
  return [...obligations]
    .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    .find((obligation) => {
      const status = computeObligationStatus(obligation, today)
      return status !== 'Paid' && status !== 'Cancelled' && status !== 'Waived'
    })
}

export function getDaysUntilDue(dueDate: string, today: number = todayTimestamp()): number {
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
  const totalPending = activeObligations.reduce((sum, obligation) => sum + getObligationAmountPending(obligation), 0)
  const totalOverdue = activeObligations.reduce((sum, obligation) => sum + getObligationAmountOverdue(obligation, today), 0)

  const nextPaymentObligation = getNextPaymentObligation(obligations, today)
  const nextPaymentDaysUntilDue = nextPaymentObligation ? getDaysUntilDue(nextPaymentObligation.dueDate, today) : undefined
  const nextPaymentIsOverdue = nextPaymentObligation ? nextPaymentDaysUntilDue !== undefined && nextPaymentDaysUntilDue < 0 : false

  return {
    contractAmount: agreement.contractAmount,
    totalReceived,
    totalPending,
    totalOverdue,
    nextPaymentObligation,
    nextPaymentDaysUntilDue,
    nextPaymentIsOverdue,
  }
}

const FREQUENCY_INTERVAL_MONTHS: Partial<Record<string, number>> = {
  Monthly: 1,
  Quarterly: 3,
  'Half-yearly': 6,
  Yearly: 12,
}

interface CreateAgreementScheduleInput {
  contractAmount: number
  contractStartDate: string
  contractEndDate?: string
  paymentFrequency: string
}

interface GeneratedObligation {
  sequenceNumber: number
  description: string
  amountDue: number
  dueDate: string
}

/**
 * Generates an even payment schedule between the contract start and end
 * dates for a given frequency — see Pass 19A section 3. 'One-time' and
 * 'Custom' schedules are created directly by the user instead (custom
 * schedules do not fit an even split).
 */
export function generateEvenSchedule(agreement: CreateAgreementScheduleInput): GeneratedObligation[] {
  if (agreement.paymentFrequency === 'One-time') {
    return [{ sequenceNumber: 1, description: 'Full payment', amountDue: agreement.contractAmount, dueDate: agreement.contractStartDate }]
  }

  const intervalMonths = FREQUENCY_INTERVAL_MONTHS[agreement.paymentFrequency]
  if (!intervalMonths || !agreement.contractEndDate) {
    return [{ sequenceNumber: 1, description: 'Full payment', amountDue: agreement.contractAmount, dueDate: agreement.contractStartDate }]
  }

  const start = new Date(agreement.contractStartDate)
  const end = new Date(agreement.contractEndDate)
  const installments: GeneratedObligation[] = []
  const cursor = new Date(start)
  let sequenceNumber = 1

  while (cursor <= end) {
    installments.push({
      sequenceNumber,
      description: `Installment ${sequenceNumber}`,
      amountDue: 0,
      dueDate: cursor.toISOString().slice(0, 10),
    })
    cursor.setMonth(cursor.getMonth() + intervalMonths)
    sequenceNumber += 1
  }

  if (installments.length === 0) {
    installments.push({ sequenceNumber: 1, description: 'Full payment', amountDue: agreement.contractAmount, dueDate: agreement.contractStartDate })
    return installments
  }

  // Split evenly, folding any rounding remainder into the final
  // installment so the schedule always sums exactly to the contract
  // amount (avoids under/over-collecting by a few cents).
  const baseAmount = Math.floor((agreement.contractAmount / installments.length) * 100) / 100
  const roundingRemainder = Math.round((agreement.contractAmount - baseAmount * installments.length) * 100) / 100

  return installments.map((installment, index) => ({
    ...installment,
    amountDue: index === installments.length - 1 ? Math.round((baseAmount + roundingRemainder) * 100) / 100 : baseAmount,
  }))
}
