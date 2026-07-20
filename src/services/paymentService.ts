import { ADJUSTMENTS } from '@/mock/adjustments'
import { FINANCIAL_AGREEMENTS } from '@/mock/financialAgreements'
import { FINANCIAL_AUDIT_EVENTS } from '@/mock/financialAuditEvents'
import { PAYMENT_ALLOCATIONS } from '@/mock/paymentAllocations'
import { PAYMENT_OBLIGATIONS } from '@/mock/paymentObligations'
import { PAYMENTS } from '@/mock/payments'
import { REFUNDS } from '@/mock/refunds'
import type {
  Adjustment,
  AdjustmentType,
  CreateAgreementInput,
  FinancialAgreement,
  FinancialAuditEvent,
  FinancialEventType,
  Payment,
  PaymentAllocation,
  PaymentObligation,
  RecordPaymentInput,
  Refund,
} from '@/types/Payment'
import { generateEvenSchedule } from '@/utils/paymentHelpers'
import { simulateNetworkDelay } from '@/utils/mockDelay'

// In-memory working copies — same "mock service holds its own state for
// the session" convention as messageService/governmentSubmissionService.
const agreements: FinancialAgreement[] = [...FINANCIAL_AGREEMENTS]
const obligations: PaymentObligation[] = [...PAYMENT_OBLIGATIONS]
const payments: Payment[] = [...PAYMENTS]
const allocations: PaymentAllocation[] = [...PAYMENT_ALLOCATIONS]
const auditEvents: FinancialAuditEvent[] = [...FINANCIAL_AUDIT_EVENTS]
const refunds: Refund[] = [...REFUNDS]
const adjustments: Adjustment[] = [...ADJUSTMENTS]

function nextId(prefix: string, existing: { id: string }[]): string {
  return `${prefix}-${String(existing.length + 1).padStart(3, '0')}`
}

function logEvent(agreementId: string, eventType: FinancialEventType, user: string, details: Partial<Pick<FinancialAuditEvent, 'previousValue' | 'newValue' | 'reason'>> = {}) {
  auditEvents.push({
    id: nextId('FAE', auditEvents),
    agreementId,
    eventType,
    user,
    timestamp: new Date().toISOString(),
    ...details,
  })
}

async function getFinancialAgreements(): Promise<FinancialAgreement[]> {
  await simulateNetworkDelay()
  return [...agreements]
}

async function getAgreementByProject(projectId: string): Promise<FinancialAgreement | undefined> {
  await simulateNetworkDelay()
  return agreements.find((agreement) => agreement.projectId === projectId)
}

async function getObligations(agreementId: string): Promise<PaymentObligation[]> {
  await simulateNetworkDelay()
  return obligations.filter((obligation) => obligation.agreementId === agreementId).sort((a, b) => a.sequenceNumber - b.sequenceNumber)
}

async function getAllObligations(): Promise<PaymentObligation[]> {
  await simulateNetworkDelay()
  return [...obligations]
}

async function getPayments(agreementId: string): Promise<Payment[]> {
  await simulateNetworkDelay()
  return payments
    .filter((payment) => payment.agreementId === agreementId)
    .sort((a, b) => b.paymentDate.localeCompare(a.paymentDate))
}

async function getAllocationsForPayment(paymentId: string): Promise<PaymentAllocation[]> {
  await simulateNetworkDelay()
  return allocations.filter((allocation) => allocation.paymentId === paymentId)
}

async function getAuditEvents(agreementId: string): Promise<FinancialAuditEvent[]> {
  await simulateNetworkDelay()
  return auditEvents
    .filter((event) => event.agreementId === agreementId)
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
}

async function getRefunds(agreementId: string): Promise<Refund[]> {
  await simulateNetworkDelay()
  return refunds.filter((refund) => refund.agreementId === agreementId)
}

async function getAdjustments(agreementId: string): Promise<Adjustment[]> {
  await simulateNetworkDelay()
  return adjustments.filter((adjustment) => adjustment.agreementId === agreementId)
}

async function createAgreement(input: CreateAgreementInput, createdBy: string): Promise<FinancialAgreement> {
  await simulateNetworkDelay()

  const agreement: FinancialAgreement = {
    id: nextId('FA', agreements),
    ...input,
  }
  agreements.push(agreement)

  const schedule = generateEvenSchedule(agreement)
  schedule.forEach((item) => {
    obligations.push({
      id: `OBL-${agreement.id.replace('FA-', '')}-${String(item.sequenceNumber).padStart(2, '0')}`,
      agreementId: agreement.id,
      sequenceNumber: item.sequenceNumber,
      description: item.description,
      amountDue: item.amountDue,
      dueDate: item.dueDate,
      amountReceived: 0,
    })
  })

  logEvent(agreement.id, 'Agreement Created', createdBy)
  schedule.forEach(() => logEvent(agreement.id, 'Obligation Created', createdBy))

  return agreement
}

async function recordPayment(input: RecordPaymentInput, createdBy: string): Promise<Payment> {
  await simulateNetworkDelay()

  const payment: Payment = {
    id: nextId('PMT', payments),
    agreementId: input.agreementId,
    projectId: input.projectId,
    amountReceived: input.amountReceived,
    paymentDate: input.paymentDate,
    paymentMode: input.paymentMode,
    referenceNumber: input.referenceNumber,
    payer: input.payer,
    notes: input.notes,
    createdBy,
    createdDate: new Date().toISOString(),
  }
  payments.push(payment)

  input.allocations.forEach((allocationInput) => {
    allocations.push({
      id: nextId('ALC', allocations),
      paymentId: payment.id,
      obligationId: allocationInput.obligationId,
      amountAllocated: allocationInput.amount,
    })
    const obligation = obligations.find((item) => item.id === allocationInput.obligationId)
    if (obligation) obligation.amountReceived += allocationInput.amount
  })

  logEvent(input.agreementId, 'Payment Received', createdBy, {
    newValue: `${input.paymentMode === 'Other' ? 'payment' : `${input.amountReceived} via ${input.paymentMode}`}`,
  })
  if (input.allocations.length > 0) {
    logEvent(input.agreementId, 'Payment Allocated', createdBy, {
      newValue: input.allocations.map((allocation) => `${allocation.amount} → ${allocation.obligationId}`).join(', '),
    })
  }

  return payment
}

async function createRefund(
  input: { agreementId: string; obligationId: string; refundAmount: number; refundDate: string; reason: string; authorisingUser: string; reference?: string },
): Promise<Refund> {
  await simulateNetworkDelay()

  const relatedAllocation = allocations.find((allocation) => allocation.obligationId === input.obligationId)

  const refund: Refund = {
    id: nextId('REF', refunds),
    paymentId: relatedAllocation?.paymentId ?? '',
    agreementId: input.agreementId,
    refundAmount: input.refundAmount,
    refundDate: input.refundDate,
    reason: input.reason,
    authorisingUser: input.authorisingUser,
    reference: input.reference,
  }
  refunds.push(refund)

  const obligation = obligations.find((item) => item.id === input.obligationId)
  if (obligation) obligation.amountReceived = Math.max(0, obligation.amountReceived - input.refundAmount)

  logEvent(input.agreementId, 'Payment Refunded', input.authorisingUser, {
    newValue: `${input.refundAmount} refunded against ${input.obligationId}`,
    reason: input.reason,
  })

  return refund
}

async function createAdjustment(
  input: { agreementId: string; obligationId: string; type: AdjustmentType; amount: number; reason: string; authorisingUser: string },
): Promise<Adjustment> {
  await simulateNetworkDelay()

  const adjustment: Adjustment = {
    id: nextId('ADJ', adjustments),
    agreementId: input.agreementId,
    type: input.type,
    amount: input.amount,
    reason: input.reason,
    authorisingUser: input.authorisingUser,
    date: new Date().toISOString().slice(0, 10),
  }
  adjustments.push(adjustment)

  const obligation = obligations.find((item) => item.id === input.obligationId)
  if (obligation) {
    const previousValue = `${obligation.description}: ${obligation.amountDue}`
    obligation.amountDue = Math.max(0, obligation.amountDue + (input.type === 'Decrease' ? -input.amount : input.amount))
    logEvent(input.agreementId, 'Adjustment Applied', input.authorisingUser, {
      previousValue,
      newValue: `${obligation.description}: ${obligation.amountDue}`,
      reason: input.reason,
    })
  }

  return adjustment
}

async function cancelObligation(obligationId: string, reason: string, user: string): Promise<void> {
  await simulateNetworkDelay()
  const obligation = obligations.find((item) => item.id === obligationId)
  if (!obligation) return
  obligation.manualStatus = 'Cancelled'
  logEvent(obligation.agreementId, 'Obligation Cancelled', user, { newValue: obligation.description, reason })
}

async function waiveObligation(obligationId: string, reason: string, user: string): Promise<void> {
  await simulateNetworkDelay()
  const obligation = obligations.find((item) => item.id === obligationId)
  if (!obligation) return
  obligation.manualStatus = 'Waived'
  logEvent(obligation.agreementId, 'Obligation Waived', user, { newValue: obligation.description, reason })
}

export const paymentService = {
  getFinancialAgreements,
  getAgreementByProject,
  getObligations,
  getAllObligations,
  getPayments,
  getAllocationsForPayment,
  getAuditEvents,
  getRefunds,
  getAdjustments,
  createAgreement,
  recordPayment,
  createRefund,
  createAdjustment,
  cancelObligation,
  waiveObligation,
}
