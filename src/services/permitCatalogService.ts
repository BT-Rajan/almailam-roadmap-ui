import { apiClient } from '@/services/httpClient'
import type { PermitCatalogItem } from '@/types/PermitCatalog'

/**
 * Fetch all permits from the backend API
 */
async function getPermits(): Promise<PermitCatalogItem[]> {
  try {
    return await apiClient.get<PermitCatalogItem[]>('/api/permit-catalog/permits')
  } catch (error) {
    console.error('Failed to fetch permit catalog:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch permits')
  }
}

/**
 * Create a new permit via backend API. The backend rejects duplicate
 * names (case-insensitive) with a 409, surfaced as a thrown Error.
 */
async function createPermit(name: string): Promise<PermitCatalogItem> {
  try {
    return await apiClient.post<PermitCatalogItem>('/api/permit-catalog/permits', { name })
  } catch (error) {
    console.error('Failed to add permit:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add permit')
  }
}

/**
 * Rename a permit via backend API
 */
async function renamePermit(permitId: string, name: string): Promise<PermitCatalogItem> {
  try {
    return await apiClient.patch<PermitCatalogItem>(`/api/permit-catalog/permits/${permitId}`, { name })
  } catch (error) {
    console.error(`Failed to rename permit ${permitId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to rename permit')
  }
}

/**
 * Remove a permit via backend API
 */
async function removePermit(permitId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/permit-catalog/permits/${permitId}`)
  } catch (error) {
    console.error(`Failed to remove permit ${permitId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove permit')
  }
}

export const permitCatalogService = {
  getPermits,
  createPermit,
  renamePermit,
  removePermit,
}
