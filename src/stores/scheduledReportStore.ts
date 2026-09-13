import { defineStore } from 'pinia'

import { scheduledReportService } from '@/services/scheduledReportService'
import type { ScheduledReport, ScheduledReportInput } from '@/types/ScheduledReport'

interface ScheduledReportStoreState {
  schedules: ScheduledReport[]
  isLoading: boolean
  error: string | undefined
}

export const useScheduledReportStore = defineStore('scheduledReport', {
  state: (): ScheduledReportStoreState => ({
    schedules: [],
    isLoading: false,
    error: undefined,
  }),

  actions: {
    async loadSchedules() {
      this.isLoading = true
      this.error = undefined
      try {
        this.schedules = await scheduledReportService.getSchedules()
      } catch (error) {
        this.error = error instanceof Error && error.message ? error.message : 'Unable to load scheduled reports. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async createSchedule(payload: ScheduledReportInput): Promise<ScheduledReport> {
      const created = await scheduledReportService.createSchedule(payload)
      this.schedules = [created, ...this.schedules]
      return created
    },

    async updateSchedule(id: string, payload: ScheduledReportInput): Promise<ScheduledReport> {
      const updated = await scheduledReportService.updateSchedule(id, payload)
      this.schedules = this.schedules.map((schedule) => (schedule.id === id ? updated : schedule))
      return updated
    },

    async deleteSchedule(id: string): Promise<void> {
      await scheduledReportService.deleteSchedule(id)
      this.schedules = this.schedules.filter((schedule) => schedule.id !== id)
    },

    async sendTestNow(id: string): Promise<void> {
      await scheduledReportService.sendTestNow(id)
    },
  },
})
