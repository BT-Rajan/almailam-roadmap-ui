import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { PagedResponse } from '@/types/Pagination'

export interface AuditLog {
  id: string
  entityType: string
  entityId: string
  eventLabel: string
  previousValue?: string
  newValue?: string
  reason?: string
  changedBy: string
  changedAt: string
}

export interface AuditLogQuery {
  entityType?: string
  entityId?: string
  changedBy?: string
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

function buildQuery(query: AuditLogQuery = {}): string {
  const params = new URLSearchParams()
  if (query.entityType) params.set('entity_type', query.entityType)
  if (query.entityId) params.set('entity_id', query.entityId)
  if (query.changedBy) params.set('changed_by', query.changedBy)
  if (query.startDate) params.set('start_date', query.startDate)
  if (query.endDate) params.set('end_date', query.endDate)
  if (query.page) params.set('page', String(query.page))
  if (query.pageSize) params.set('pageSize', String(query.pageSize))
  const queryString = params.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * Audit logging service for the Administration audit log viewer
 */
class AuditService {
  /**
   * Get a page of audit logs with optional filtering
   */
  async getLogs(query?: AuditLogQuery): Promise<PagedResponse<AuditLog>> {
    try {
      return await apiClient.get<PagedResponse<AuditLog>>(`/api/audit-logs${buildQuery(query)}`)
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch audit logs')
    }
  }

  /**
   * Get audit logs for a specific entity
   */
  async getEntityLogs(entityType: string, entityId: string): Promise<AuditLog[]> {
    const result = await this.getLogs({ entityType, entityId, pageSize: 200 })
    return result.items
  }

  /**
   * Get audit logs for a specific user
   */
  async getUserLogs(userId: string, pageSize = 50): Promise<AuditLog[]> {
    const result = await this.getLogs({ changedBy: userId, pageSize })
    return result.items
  }

  /**
   * Get recent activity (last N logs)
   */
  async getRecentActivity(pageSize = 20): Promise<AuditLog[]> {
    const result = await this.getLogs({ pageSize })
    return result.items
  }

  /**
   * Export audit logs as a CSV file (backend generates the CSV)
   */
  async exportLogs(query?: Pick<AuditLogQuery, 'entityType' | 'startDate' | 'endDate'>): Promise<Blob> {
    try {
      const authStore = useAuthStore()
      const params = new URLSearchParams()
      if (query?.entityType) params.set('entity_type', query.entityType)
      if (query?.startDate) params.set('start_date', query.startDate)
      if (query?.endDate) params.set('end_date', query.endDate)

      const response = await fetch(`/api/audit-logs/export?${params.toString()}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${authStore.accessToken ?? ''}`,
        },
      })

      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`)
      }

      return await response.blob()
    } catch (error) {
      console.error('Failed to export audit logs:', error)
      throw new Error(error instanceof Error ? error.message : 'Failed to export audit logs')
    }
  }
}

export const auditService = new AuditService()
