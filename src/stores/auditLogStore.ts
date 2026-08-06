import { defineStore } from 'pinia'

import { auditService } from '@/services/auditService'
import type { AuditLog } from '@/services/auditService'

interface AuditLogPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface AuditLogStoreState {
  logs: AuditLog[]
  isLoading: boolean
  error: string | undefined
  entityTypeFilter: string | 'All'
  pagination: AuditLogPaginationState
}

export const useAuditLogStore = defineStore('auditLog', {
  state: (): AuditLogStoreState => ({
    logs: [],
    isLoading: false,
    error: undefined,
    entityTypeFilter: 'All',
    pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
  }),

  actions: {
    async loadLogs() {
      this.isLoading = true
      this.error = undefined
      try {
        const result = await auditService.getLogs({
          entityType: this.entityTypeFilter !== 'All' ? this.entityTypeFilter : undefined,
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
        })
        this.logs = result.items
        this.pagination = {
          page: result.page,
          pageSize: result.pageSize,
          total: result.total,
          totalPages: result.totalPages,
        }
      } catch {
        this.error = 'Unable to load the audit log. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    setPage(page: number) {
      this.pagination.page = page
      void this.loadLogs()
    },

    setPageSize(size: number) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      void this.loadLogs()
    },

    setEntityTypeFilter(entityType: string | 'All') {
      this.entityTypeFilter = entityType
      this.pagination.page = 1
      void this.loadLogs()
    },

    async exportCsv() {
      const blob = await auditService.exportLogs({
        entityType: this.entityTypeFilter !== 'All' ? this.entityTypeFilter : undefined,
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'audit-log-export.csv'
      link.click()
      URL.revokeObjectURL(url)
    },
  },
})
