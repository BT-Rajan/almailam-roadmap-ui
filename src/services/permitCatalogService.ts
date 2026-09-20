import { apiClient, asError } from '@/services/httpClient'
import type { PermitApplicationSetupInput, PermitCatalogItem, PermitPrerequisite } from '@/types/PermitCatalog'

/**
 * Fetch all permits from the backend API
 */
async function getPermits(): Promise<PermitCatalogItem[]> {
  try {
    return await apiClient.get<PermitCatalogItem[]>('/api/permit-catalog/permits')
  } catch (error) {
    console.error('Failed to fetch permit catalog:', error)
    throw asError(error, 'Failed to fetch permits')
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
    throw asError(error, 'Failed to add permit')
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
    throw asError(error, 'Failed to rename permit')
  }
}

/**
 * Set which authority, form and checklist a permit type's applications
 * use -- replaces the whole setup; null authority/form unmaps it.
 */
async function setApplicationSetup(permitId: string, setup: PermitApplicationSetupInput): Promise<PermitCatalogItem> {
  try {
    return await apiClient.put<PermitCatalogItem>(`/api/permit-catalog/permits/${permitId}/application-setup`, setup)
  } catch (error) {
    console.error(`Failed to save application setup for permit ${permitId}:`, error)
    throw asError(error, 'Failed to save the application setup')
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
    throw asError(error, 'Failed to remove permit')
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
    throw asError(error, 'Failed to fetch permit prerequisites')
  }
}

async function addPrerequisite(permitId: string, designActivityId: string): Promise<PermitPrerequisite> {
  try {
    return await apiClient.post<PermitPrerequisite>(`/api/permit-catalog/permits/${permitId}/prerequisites`, {
      designActivityId,
    })
  } catch (error) {
    console.error(`Failed to add prerequisite to permit ${permitId}:`, error)
    throw asError(error, 'Failed to add permit prerequisite')
  }
}

async function removePrerequisite(prerequisiteId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/permit-catalog/prerequisites/${prerequisiteId}`)
  } catch (error) {
    console.error(`Failed to remove prerequisite ${prerequisiteId}:`, error)
    throw asError(error, 'Failed to remove permit prerequisite')
  }
}

export const permitCatalogService = {
  getPermits,
  createPermit,
  renamePermit,
  setApplicationSetup,
  removePermit,
  getPrerequisites,
  addPrerequisite,
  removePrerequisite,
}
