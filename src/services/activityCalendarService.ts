import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'

/**
 * Activity update types
 */
export enum ActivityType {
  NEW = 'new',
  UPDATED = 'updated',
  DELAYED = 'delayed',
  COMPLETED = 'completed',
  ASSIGNED = 'assigned',
  COMMENTED = 'commented',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

/**
 * Entity types for activities
 */
export enum EntityType {
  PROJECT = 'project',
  CLIENT = 'client',
  QUOTATION = 'quotation',
  CONTRACT = 'contract',
  DOCUMENT = 'document',
  TASK = 'task',
  PAYMENT = 'payment',
  WORKFLOW = 'workflow',
}

/**
 * Activity record
 */
export interface ActivityRecord {
  id: string
  type: ActivityType
  entityType: EntityType
  entityId: string
  entityName: string
  projectId?: string
  projectName?: string
  userId: string
  userName: string
  description: string
  timestamp: string
  changes?: Record<string, unknown>
}

/**
 * Daily activity summary
 */
export interface DailySummary {
  date: string
  new: number
  updated: number
  delayed: number
  completed: number
  assigned: number
  commented: number
  approved: number
  rejected: number
  total: number
  activities: ActivityRecord[]
}

/**
 * Activity filter criteria
 */
export interface ActivityFilter {
  startDate: string
  endDate: string
  projectId?: string
  userId?: string
  type?: ActivityType
}

/**
 * Fetch activity summary for a specific date
 */
async function getDayActivity(date: string): Promise<DailySummary> {
  try {
    return await apiClient.get<DailySummary>(`/api/admin/activity/day/${date}`)
  } catch (error) {
    console.error(`Failed to fetch day activity for ${date}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch day activity')
  }
}

/**
 * Fetch activity summary for a month
 */
async function getMonthActivity(month: string): Promise<DailySummary[]> {
  try {
    // month format: YYYY-MM
    return await apiClient.get<DailySummary[]>(`/api/admin/activity/month/${month}`)
  } catch (error) {
    console.error(`Failed to fetch month activity for ${month}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch month activity')
  }
}

/**
 * Fetch activities with custom filters
 */
async function getFilteredActivities(filter: ActivityFilter): Promise<ActivityRecord[]> {
  try {
    const params = new URLSearchParams()
    params.append('startDate', filter.startDate)
    params.append('endDate', filter.endDate)
    if (filter.projectId) params.append('projectId', filter.projectId)
    if (filter.userId) params.append('userId', filter.userId)
    if (filter.type) params.append('type', filter.type)

    return await apiClient.get<ActivityRecord[]>(`/api/admin/activity/filtered?${params.toString()}`)
  } catch (error) {
    console.error('Failed to fetch filtered activities:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch activities')
  }
}

/**
 * Get all projects for activity filtering
 */
async function getProjectsForFiltering(): Promise<Array<{ id: string; name: string }>> {
  try {
    return await apiClient.get<Array<{ id: string; name: string }>>('/api/admin/activity/projects')
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch projects')
  }
}

/**
 * Get all users for activity filtering
 */
async function getUsersForFiltering(): Promise<Array<{ id: string; name: string }>> {
  try {
    return await apiClient.get<Array<{ id: string; name: string }>>('/api/admin/activity/users')
  } catch (error) {
    console.error('Failed to fetch users:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch users')
  }
}

/**
 * Export activities to CSV
 */
async function exportActivitiesCSV(filter: ActivityFilter): Promise<Blob> {
  try {
    const params = new URLSearchParams()
    params.append('startDate', filter.startDate)
    params.append('endDate', filter.endDate)
    if (filter.projectId) params.append('projectId', filter.projectId)
    if (filter.userId) params.append('userId', filter.userId)
    if (filter.type) params.append('type', filter.type)

    // apiClient (httpClient.ts) always parses the response as JSON, so it
    // can't return a file blob -- fetch directly here instead, same
    // approach as auditService.ts's CSV export.
    const authStore = useAuthStore()
    const response = await fetch(`/api/admin/activity/export/csv?${params.toString()}`, {
      headers: { Authorization: `Bearer ${authStore.accessToken ?? ''}` },
    })
    if (!response.ok) {
      throw new Error(`Export failed with status ${response.status}`)
    }
    return await response.blob()
  } catch (error) {
    console.error('Failed to export activities:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to export activities')
  }
}

export const activityCalendarService = {
  getDayActivity,
  getMonthActivity,
  getFilteredActivities,
  getProjectsForFiltering,
  getUsersForFiltering,
  exportActivitiesCSV,
}
