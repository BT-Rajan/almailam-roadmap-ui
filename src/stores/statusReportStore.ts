import { defineStore } from 'pinia'

import { statusReportService } from '@/services/statusReportService'
import type { StatusReportAttachInput } from '@/services/statusReportService'
import type { StatusReport } from '@/types/StatusReport'

interface StatusReportInboxState {
  reports: StatusReport[]
  isLoading: boolean
  error: string | undefined
}

export const useStatusReportStore = defineStore('statusReportInbox', {
  state: (): StatusReportInboxState => ({
    reports: [],
    isLoading: false,
    error: undefined,
  }),

  actions: {
    async loadInbox() {
      this.isLoading = true
      this.error = undefined
      try {
        this.reports = await statusReportService.getInbox()
      } catch {
        this.error = 'Unable to load the status report inbox. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async attachReport(reportId: string, input: StatusReportAttachInput) {
      await statusReportService.attachReport(reportId, input)
      // Attached reports leave the inbox -- this removes it from the
      // list rather than re-fetching the whole inbox for one change.
      this.reports = this.reports.filter((r) => r.id !== reportId)
    },
  },
})
