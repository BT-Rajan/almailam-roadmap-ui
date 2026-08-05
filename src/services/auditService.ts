import { apiClient } from '@/services/httpClient'

export interface AuditLog {
  id: string
  entity_type: string
  entity_id: string
  event_label: string
  previous_value?: string
  new_value?: string
  reason?: string
  changed_by: string
  changed_at: string
}

export interface AuditLogQuery {
  entity_type?: string
  entity_id?: string
  changed_by?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

/**
 * Audit logging service for tracking all user actions in the system
 */
class AuditService {
  /**
   * Get audit logs with optional filtering
   */
  async getLogs(query?: AuditLogQuery): Promise<AuditLog[]> {
    try {
      const params = new URLSearchParams()
      if (query?.entity_type) params.append('entity_type', query.entity_type)
      if (query?.entity_id) params.append('entity_id', query.entity_id)
      if (query?.changed_by) params.append('changed_by', query.changed_by)
      if (query?.start_date) params.append('start_date', query.start_date)
      if (query?.end_date) params.append('end_date', query.end_date)
      if (query?.limit) params.append('limit', String(query.limit))
      if (query?.offset) params.append('offset', String(query.offset))

      const queryString = params.toString()
      const url = queryString ? `/api/audit-logs?${queryString}` : '/api/audit-logs'

      return await apiClient.get<AuditLog[]>(url)
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch audit logs')
    }
  }

  /**
   * Get audit logs for a specific entity
   */
  async getEntityLogs(entityType: string, entityId: string): Promise<AuditLog[]> {
    try {
      return await apiClient.get<AuditLog[]>(
        `/api/audit-logs?entity_type=${entityType}&entity_id=${entityId}`
      )
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch entity audit logs')
    }
  }

  /**
   * Get audit logs for a specific user
   */
  async getUserLogs(userId: string, limit = 50): Promise<AuditLog[]> {
    try {
      return await apiClient.get<AuditLog[]>(
        `/api/audit-logs?changed_by=${userId}&limit=${limit}`
      )
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch user audit logs')
    }
  }

  /**
   * Get recent activity (last N logs)
   */
  async getRecentActivity(limit = 20): Promise<AuditLog[]> {
    try {
      return await apiClient.get<AuditLog[]>(`/api/audit-logs?limit=${limit}`)
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to fetch recent activity')
    }
  }

  /**
   * Export audit logs (backend should handle CSV/JSON generation)
   */
  async exportLogs(format: 'csv' | 'json' = 'csv', query?: AuditLogQuery): Promise<Blob> {
    try {
      const params = new URLSearchParams()
      params.append('format', format)
      if (query?.entity_type) params.append('entity_type', query.entity_type)
      if (query?.start_date) params.append('start_date', query.start_date)
      if (query?.end_date) params.append('end_date', query.end_date)

      const response = await fetch(`/api/audit-logs/export?${params.toString()}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('almailam-access-token') || ''}`,
        },
      })

      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`)
      }

      return await response.blob()
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to export audit logs')
    }
  }
}

export const auditService = new AuditService()
