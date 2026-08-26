import { apiClient } from '@/services/httpClient'
import type { TypeActivityCategory, TypeActivityItem } from '@/types/TypeActivityCatalog'

/**
 * Fetch all type-activity categories (with their activities) from the
 * backend API -- same shape/error-handling convention as
 * serviceCatalogService.getServices.
 */
async function getCategories(): Promise<TypeActivityCategory[]> {
  try {
    return await apiClient.get<TypeActivityCategory[]>('/api/type-activity-catalog/categories')
  } catch (error) {
    console.error('Failed to fetch type activity catalog:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch type activity categories')
  }
}

async function createCategory(name: string): Promise<TypeActivityCategory> {
  try {
    return await apiClient.post<TypeActivityCategory>('/api/type-activity-catalog/categories', { name })
  } catch (error) {
    console.error('Failed to add type activity category:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add category')
  }
}

async function renameCategory(categoryId: string, name: string): Promise<TypeActivityCategory> {
  try {
    return await apiClient.patch<TypeActivityCategory>(`/api/type-activity-catalog/categories/${categoryId}`, { name })
  } catch (error) {
    console.error(`Failed to rename type activity category ${categoryId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to rename category')
  }
}

async function removeCategory(categoryId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/type-activity-catalog/categories/${categoryId}`)
  } catch (error) {
    console.error(`Failed to remove type activity category ${categoryId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove category')
  }
}

async function addActivity(categoryId: string, name: string, cost: number): Promise<TypeActivityItem> {
  try {
    return await apiClient.post<TypeActivityItem>(`/api/type-activity-catalog/categories/${categoryId}/activities`, {
      name,
      cost,
    })
  } catch (error) {
    console.error('Failed to add type activity:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add activity')
  }
}

async function updateActivity(
  activityId: string,
  fields: Partial<Pick<TypeActivityItem, 'name' | 'cost'>>,
): Promise<TypeActivityItem> {
  try {
    return await apiClient.patch<TypeActivityItem>(`/api/type-activity-catalog/activities/${activityId}`, fields)
  } catch (error) {
    console.error(`Failed to update type activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update activity')
  }
}

async function removeActivity(activityId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/type-activity-catalog/activities/${activityId}`)
  } catch (error) {
    console.error(`Failed to remove type activity ${activityId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to remove activity')
  }
}

export const typeActivityCatalogService = {
  getCategories,
  createCategory,
  renameCategory,
  removeCategory,
  addActivity,
  updateActivity,
  removeActivity,
}
