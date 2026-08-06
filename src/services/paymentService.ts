import { apiClient } from '@/services/httpClient'
import type {
  Adjustment,
  AdjustmentType,
  CreateAgreementInput,
  FinancialAgreement,
  FinancialAuditEvent,
  Payment,
  PaymentAllocation,
  PaymentObligation,
  RecordPaymentInput,
  Refund,
} from '@/types/Payment'

/**
 * Fetch all financial agreements via the backend API
 */
async function getFinancialAgreements(): Promise<FinancialAgreement[]> {
  try {
    return await apiClient.get<FinancialAgreement[]>('/api/financial-agreements')
  } catch (error) {
    console.error('Failed to fetch agreements:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch agreements')
  }
}

/**
 * Get the financial agreement for a specific project via the backend API
 */
async function getAgreementByProject(projectId: string): Promise<FinancialAgreement | undefined> {
  try {
    const agreement = await apiClient.get<FinancialAgreement | null>(
      `/api/financial-agreements/by-project/${projectId}`,
    )
    return agreement ?? undefined
  } catch (error) {
    console.error(`Failed to fetch agreement for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch agreement')
  }
}

/**
 * Get payment obligations for a single agreement via the backend API
 */
async function getObligations(agreementId: string): Promise<PaymentObligation[]> {
  try {
    return await apiClient.get<PaymentObligation[]>(`/api/financial-agreements/${agreementId}/obligations`)
  } catch (error) {
    console.error('Failed to fetch obligations:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch obligations')
  }
}

/**
 * Get every payment obligation across all agreements via the backend API
 */
async function getAllObligations(): Promise<PaymentObligation[]> {
  try {
    return await apiClient.get<PaymentObligation[]>('/api/obligations')
  } catch (error) {
    console.error('Failed to fetch all obligations:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch obligations')
  }
}

/**
 * Get payments for an agreement via the backend API
 */
async function getPayments(agreementId: string): Promise<Payment[]> {
  try {
    return await apiClient.get<Payment[]>(`/api/financial-agreements/${agreementId}/payments`)
  } catch (error) {
    console.error('Failed to fetch payments:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch payments')
  }
}

/**
 * Get payment allocations for a specific payment via the backend API
 */
async function getAllocationsForPayment(paymentId: string): Promise<PaymentAllocation[]> {
  try {
    return await apiClient.get<PaymentAllocation[]>(`/api/payments/${paymentId}/allocations`)
  } catch (error) {
    console.error('Failed to fetch allocations:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch allocations')
  }
}

/**
 * Get audit events for an agreement via the backend API
 */
async function getAuditEvents(agreementId: string): Promise<FinancialAuditEvent[]> {
  try {
    return await apiClient.get<FinancialAuditEvent[]>(`/api/financial-agreements/${agreementId}/audit-events`)
  } catch (error) {
    console.error('Failed to fetch audit events:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch audit events')
  }
}

/**
 * Get refunds for an agreement via the backend API
 */
async function getRefunds(agreementId: string): Promise<Refund[]> {
  try {
    return await apiClient.get<Refund[]>(`/api/financial-agreements/${agreementId}/refunds`)
  } catch (error) {
    console.error('Failed to fetch refunds:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch refunds')
  }
}

/**
 * Get adjustments for an agreement via the backend API
 */
async function getAdjustments(agreementId: string): Promise<Adjustment[]> {
  try {
    return await apiClient.get<Adjustment[]>(`/api/financial-agreements/${agreementId}/adjustments`)
  } catch (error) {
    console.error('Failed to fetch adjustments:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch adjustments')
  }
}

/**
 * Create a new financial agreement via the backend API.
 * The authorised user is derived server-side from the auth token, so
 * `createdBy` is accepted for interface stability but not sent.
 */
async function createAgreement(input: CreateAgreementInput, _createdBy: string): Promise<FinancialAgreement> {
  void _createdBy
  try {
    return await apiClient.post<FinancialAgreement>('/api/financial-agreements', input)
  } catch (error) {
    console.error('Failed to create agreement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create agreement')
  }
}

/**
 * Record a payment via the backend API.
 * The authorised user is derived server-side from the auth token, so
 * `createdBy` is accepted for interface stability but not sent.
 */
async function recordPayment(input: RecordPaymentInput, _createdBy: string): Promise<Payment> {
  void _createdBy
  try {
    return await apiClient.post<Payment>('/api/payments', input)
  } catch (error) {
    console.error('Failed to record payment:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record payment')
  }
}

interface CreateRefundInput {
  agreementId: string
  obligationId: string
  refundAmount: number
  refundDate: string
  reason: string
  authorisingUser: string
  reference?: string
}

/**
 * Create a refund against an obligation via the backend API
 */
async function createRefund(input: CreateRefundInput): Promise<Refund> {
  try {
    return await apiClient.post<Refund>(`/api/financial-agreements/${input.agreementId}/refunds`, {
      obligationId: input.obligationId,
      refundAmount: input.refundAmount,
      refundDate: input.refundDate,
      reason: input.reason,
      reference: input.reference,
    })
  } catch (error) {
    console.error('Failed to create refund:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create refund')
  }
}

interface CreateAdjustmentInput {
  agreementId: string
  obligationId: string
  type: AdjustmentType
  amount: number
  reason: string
  authorisingUser: string
}

/**
 * Create an adjustment against an obligation via the backend API
 */
async function createAdjustment(input: CreateAdjustmentInput): Promise<Adjustment> {
  try {
    return await apiClient.post<Adjustment>(`/api/financial-agreements/${input.agreementId}/adjustments`, {
      obligationId: input.obligationId,
      type: input.type,
      amount: input.amount,
      reason: input.reason,
    })
  } catch (error) {
    console.error('Failed to create adjustment:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create adjustment')
  }
}

/**
 * Cancel a payment obligation via the backend API.
 * The authorised user is derived server-side from the auth token, so
 * `user` is accepted for interface stability but not sent.
 */
async function cancelObligation(obligationId: string, reason: string, _user: string): Promise<void> {
  void _user
  try {
    await apiClient.patch(`/api/obligations/${obligationId}/override`, {
      status: 'Cancelled',
      reason,
    })
  } catch (error) {
    console.error('Failed to cancel obligation:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to cancel obligation')
  }
}

/**
 * Waive a payment obligation via the backend API.
 * The authorised user is derived server-side from the auth token, so
 * `user` is accepted for interface stability but not sent.
 */
async function waiveObligation(obligationId: string, reason: string, _user: string): Promise<void> {
  void _user
  try {
    await apiClient.patch(`/api/obligations/${obligationId}/override`, {
      status: 'Waived',
      reason,
    })
  } catch (error) {
    console.error('Failed to waive obligation:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to waive obligation')
  }
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
