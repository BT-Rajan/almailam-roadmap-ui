import { apiClient } from '@/services/httpClient'
import type { Quotation } from '@/types/Quotation'

/**
 * Fetch quotations for a specific project from backend API
 */
async function getQuotationsByProject(projectId: string): Promise<Quotation[]> {
  try {
    return await apiClient.get<Quotation[]>(`/api/quotations?projectId=${projectId}`)
  } catch (error) {
    console.error(`Failed to fetch quotations for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch quotations')
  }
}

/**
 * Fetch a specific quotation by ID from backend API
 */
async function getQuotationById(quotationId: string): Promise<Quotation | undefined> {
  try {
    return await apiClient.get<Quotation>(`/api/quotations/${quotationId}`)
  } catch (error) {
    console.error(`Failed to fetch quotation ${quotationId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch quotation')
  }
}

/**
 * Fetch all quotations from backend API
 */
async function getQuotations(): Promise<Quotation[]> {
  try {
    return await apiClient.get<Quotation[]>('/api/quotations')
  } catch (error) {
    console.error('Failed to fetch quotations:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch quotations')
  }
}

export interface QuotationLineItemInput {
  description: string
  quantity: number
  unitPrice: number
}

export interface QuotationCreateInput {
  projectId: string
  validity: string
  currency: string
  taxRatePercent: number
  discountAmount: number
  notes?: string
  termsAndConditions: string[]
  lineItems: QuotationLineItemInput[]
  templateKey?: string
  clientRepresentative?: string
  subjectLine?: string
  projectReference?: string
  feeFrequency?: string
  scopeItems?: string[]
  paymentTerms?: string[]
}

/**
 * Create a new quotation via backend API
 */
async function createQuotation(quotationData: QuotationCreateInput): Promise<Quotation> {
  try {
    return await apiClient.post<Quotation>('/api/quotations', quotationData)
  } catch (error) {
    console.error('Failed to create quotation:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create quotation')
  }
}

/**
 * Update a quotation via backend API
 */
async function updateQuotation(quotationId: string, quotationData: Partial<Quotation>): Promise<Quotation> {
  try {
    return await apiClient.patch<Quotation>(`/api/quotations/${quotationId}`, quotationData)
  } catch (error) {
    console.error(`Failed to update quotation ${quotationId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update quotation')
  }
}

/**
 * Delete a quotation via backend API
 */
async function deleteQuotation(quotationId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/quotations/${quotationId}`)
  } catch (error) {
    console.error(`Failed to delete quotation ${quotationId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete quotation')
  }
}

/**
 * Lock a quotation's content and mark it ready to print/send.
 */
async function finalizeQuotation(quotationId: string): Promise<Quotation> {
  try {
    return await apiClient.post<Quotation>(`/api/quotations/${quotationId}/finalize`, {})
  } catch (error) {
    console.error(`Failed to finalize quotation ${quotationId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to finalize quotation')
  }
}

/**
 * Unlock a finalized quotation for further editing.
 */
async function reopenQuotation(quotationId: string): Promise<Quotation> {
  try {
    return await apiClient.post<Quotation>(`/api/quotations/${quotationId}/reopen`, {})
  } catch (error) {
    console.error(`Failed to reopen quotation ${quotationId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to reopen quotation')
  }
}

export const quotationService = {
  getQuotationsByProject,
  getQuotationById,
  getQuotations,
  createQuotation,
  updateQuotation,
  deleteQuotation,
  finalizeQuotation,
  reopenQuotation,
}
