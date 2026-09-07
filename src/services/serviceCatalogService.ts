import { apiClient } from '@/services/httpClient'
import type { ServiceCatalogActivity, ServiceCatalogBranch, ServiceCatalogItem, SupervisionPrerequisite } from '@/types/ServiceCatalog'

/**
 * Fetch all services (with their activities) from the backend API
 */
async function getServices(): Promise<ServiceCatalogItem[]> {
  try {
    return await apiClient.get<ServiceCatalogItem[]>('/api/service-catalog/services')
  } catch (error) {
    console.error('Failed to fetch service catalog:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch services')
  }
}

/**
 * Create a new service via backend API. The backend rejects duplicate
 * names (case-insensitive) with a 409, surfaced as a thrown Error.
 */
async function createService(name: string, branch: ServiceCatalogBranch): Promise<ServiceCatalogItem> {
  try {
    return await apiClient.post<ServiceCatalogItem>('/api/service-catalog/services', { name, branch })
  } catch (error) {
    console.error('Failed to add service:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add service')
  }
}

/**
 * Rename a service via backend API
 */
async function renameService(serviceId: string, name: string): Promise<ServiceCatalogItem> {
  try {
    return await apiClient.patch<ServiceCatalogItem>(`/api/service-catalog/services/${serviceId}`, { name })
  } catch (error) {
    console.error(`Failed to rename service ${serviceId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to rename service')
  }
}

/**
 * Remove a service (and its activities) via backend API
 */
async function removeService(serviceId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/service-catalog/services/${serviceId}`)
  } catch (error) {
    console.error(`Failed to remove service ${serviceId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove service')
  }
}

/**
 * Add an activity (sub-service) with a fixed cost under a service
 */
async function addActivity(serviceId: string, name: string, fixedCost: number): Promise<ServiceCatalogActivity> {
  try {
    return await apiClient.post<ServiceCatalogActivity>(`/api/service-catalog/services/${serviceId}/activities`, {
      name,
      fixedCost,
    })
  } catch (error) {
    console.error('Failed to add activity:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add activity')
  }
}

/**
 * Update an activity's name and/or fixed cost via backend API
 */
async function updateActivity(
  activityId: string,
  fields: Partial<Pick<ServiceCatalogActivity, 'name' | 'fixedCost'>>,
): Promise<ServiceCatalogActivity> {
  try {
    return await apiClient.patch<ServiceCatalogActivity>(`/api/service-catalog/activities/${activityId}`, fields)
  } catch (error) {
    console.error(`Failed to update activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update activity')
  }
}

/**
 * Remove an activity via backend API
 */
async function removeActivity(activityId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/service-catalog/activities/${activityId}`)
  } catch (error) {
    console.error(`Failed to remove activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove activity')
  }
}

/**
 * Fetch a Supervision activity's Design-activity prerequisites via
 * backend API -- see SupervisionPrerequisite / project_service.
 * _recompute_supervision_eligibility.
 */
async function getSupervisionPrerequisites(activityId: string): Promise<SupervisionPrerequisite[]> {
  try {
    return await apiClient.get<SupervisionPrerequisite[]>(
      `/api/service-catalog/activities/${activityId}/supervision-prerequisites`,
    )
  } catch (error) {
    console.error(`Failed to fetch prerequisites for supervision activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch supervision prerequisites')
  }
}

async function addSupervisionPrerequisite(
  activityId: string, designActivityId: string,
): Promise<SupervisionPrerequisite> {
  try {
    return await apiClient.post<SupervisionPrerequisite>(
      `/api/service-catalog/activities/${activityId}/supervision-prerequisites`, { designActivityId },
    )
  } catch (error) {
    console.error(`Failed to add prerequisite to supervision activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add supervision prerequisite')
  }
}

async function removeSupervisionPrerequisite(prerequisiteId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/service-catalog/supervision-prerequisites/${prerequisiteId}`)
  } catch (error) {
    console.error(`Failed to remove prerequisite ${prerequisiteId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove supervision prerequisite')
  }
}

export const serviceCatalogService = {
  getServices,
  createService,
  renameService,
  removeService,
  addActivity,
  updateActivity,
  removeActivity,
  getSupervisionPrerequisites,
  addSupervisionPrerequisite,
  removeSupervisionPrerequisite,
}
