import { apiClient } from '@/services/httpClient'
import type { Quotation } from '@/types/Quotation'

/**
 * Fetch quotations for a specific project from backend API
 */
async function getQuotationsByProject(projectId: string): Promise<Quotation[]> {
  try {
    return await apiClient.get<Quotation[]>(`/api/projects/${projectId}/quotations`)
  } catch (error) {
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
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch quotations')
  }
}

/**
 * Create a new quotation via backend API
 */
async function createQuotation(quotationData: Partial<Quotation>): Promise<Quotation> {
  try {
    return await apiClient.post<Quotation>('/api/quotations', quotationData)
  } catch (error) {
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
    throw new Error(error instanceof Error ? error.message : 'Failed to delete quotation')
  }
}

export const quotationService = {
  getQuotationsByProject,
  getQuotationById,
  getQuotations,
  createQuotation,
  updateQuotation,
  deleteQuotation,
}
