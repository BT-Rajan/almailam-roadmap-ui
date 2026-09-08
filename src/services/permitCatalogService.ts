import { apiClient } from '@/services/httpClient'
import type { PermitCatalogItem, PermitPrerequisite } from '@/types/PermitCatalog'

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
async function createPermit(name: string, fixedCost: number): Promise<PermitCatalogItem> {
  try {
    return await apiClient.post<PermitCatalogItem>('/api/permit-catalog/permits', { name, fixedCost })
  } catch (error) {
    console.error('Failed to add permit:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add permit')
  }
}

/**
 * Rename (and re-price) a permit via backend API
 */
async function renamePermit(permitId: string, name: string, fixedCost: number): Promise<PermitCatalogItem> {
  try {
    return await apiClient.patch<PermitCatalogItem>(`/api/permit-catalog/permits/${permitId}`, { name, fixedCost })
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

/**
 * Fetch a permit's Design-activity prerequisites via backend API --
 * see PermitPrerequisite / project_service._recompute_permit_eligibility.
 */
async function getPrerequisites(permitId: string): Promise<PermitPrerequisite[]> {
  try {
    return await apiClient.get<PermitPrerequisite[]>(`/api/permit-catalog/permits/${permitId}/prerequisites`)
  } catch (error) {
    console.error(`Failed to fetch prerequisites for permit ${permitId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch permit prerequisites')
  }
}

async function addPrerequisite(permitId: string, designActivityId: string): Promise<PermitPrerequisite> {
  try {
    return await apiClient.post<PermitPrerequisite>(`/api/permit-catalog/permits/${permitId}/prerequisites`, {
      designActivityId,
    })
  } catch (error) {
    console.error(`Failed to add prerequisite to permit ${permitId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add permit prerequisite')
  }
}

async function removePrerequisite(prerequisiteId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/permit-catalog/prerequisites/${prerequisiteId}`)
  } catch (error) {
    console.error(`Failed to remove prerequisite ${prerequisiteId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove permit prerequisite')
  }
}

export const permitCatalogService = {
  getPermits,
  createPermit,
  renamePermit,
  removePermit,
  getPrerequisites,
  addPrerequisite,
  removePrerequisite,
}
