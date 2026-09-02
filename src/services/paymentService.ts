import { useAuthStore } from '@/stores/authStore'
import { apiClient } from '@/services/httpClient'
import type {
  Adjustment,
  AdjustmentType,
  AgreementStream,
  CreateAgreementInput,
  FinancialAgreement,
  FinancialAuditEvent,
  Payment,
  PaymentAllocation,
  PaymentObligation,
  RecordPaymentInput,
  Refund,
  UpdateAgreementInput,
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
 * Get the financial agreement for a specific project (optionally scoped to
 * one billing stream) via the backend API. A project can have one Design
 * and one Supervision agreement side by side, so callers that care about a
 * specific one should always pass `stream`.
 */
async function getAgreementByProject(projectId: string, stream?: AgreementStream): Promise<FinancialAgreement | undefined> {
  try {
    const query = stream ? `?stream=${stream}` : ''
    const agreement = await apiClient.get<FinancialAgreement | null>(
      `/api/financial-agreements/by-project/${projectId}${query}`,
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

/** Approves a Draft financial agreement -- see AgreementStatus. This is
 * what project_service._assert_stage_exit_criteria's Payment Plan ->
 * Contract check waits on, not the agreement's mere existence. */
async function approveAgreement(agreementId: string): Promise<FinancialAgreement> {
  try {
    return await apiClient.post<FinancialAgreement>(`/api/financial-agreements/${agreementId}/approve`)
  } catch (error) {
    console.error('Failed to approve agreement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to approve agreement')
  }
}

/**
 * Edits a Draft financial agreement's terms and regenerates its
 * installment schedule -- rejected by the backend once the agreement is
 * Approved or already has payments recorded (see payment_service.
 * _assert_agreement_editable).
 */
async function updateAgreement(agreementId: string, input: UpdateAgreementInput): Promise<FinancialAgreement> {
  try {
    return await apiClient.patch<FinancialAgreement>(`/api/financial-agreements/${agreementId}`, input)
  } catch (error) {
    console.error('Failed to update agreement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update agreement')
  }
}

/**
 * Deletes a Draft financial agreement (and its obligations) -- same
 * editability guard as updateAgreement.
 */
async function deleteAgreement(agreementId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/financial-agreements/${agreementId}`)
  } catch (error) {
    console.error('Failed to delete agreement:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete agreement')
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

/**
 * Attaches a proof-of-payment file to an already-recorded Payment --
 * the one thing addable to a Payment after the fact (it has no
 * update/delete endpoint otherwise). Multipart, so this goes through a
 * raw fetch with manual token/refresh handling rather than the JSON
 * apiClient, same reasoning and 401-retry shape as documentService.
 * uploadDocument.
 */
async function attachPaymentProof(paymentId: string, file: File): Promise<Payment> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)

  const doRequest = () =>
    fetch(`/api/payments/${paymentId}/proof`, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`)
    }
    return (await response.json()) as Payment
  } catch (error) {
    console.error(`Failed to attach proof to payment ${paymentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to attach payment proof')
  }
}

/**
 * Downloads an already-attached proof-of-payment file as a Blob --
 * caller (paymentStore) hands this to triggerBlobDownload. Same
 * authenticated-fetch shape as documentService.downloadDocument, since
 * the download route is permission-gated, not a public static file.
 */
async function downloadPaymentProof(paymentId: string): Promise<Blob> {
  const authStore = useAuthStore()

  const doRequest = () =>
    fetch(`/api/payments/${paymentId}/proof/download`, {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }
    return await response.blob()
  } catch (error) {
    console.error(`Failed to download proof for payment ${paymentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to download payment proof')
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
  updateAgreement,
  deleteAgreement,
  approveAgreement,
  recordPayment,
  attachPaymentProof,
  downloadPaymentProof,
  createRefund,
  createAdjustment,
  cancelObligation,
  waiveObligation,
}
