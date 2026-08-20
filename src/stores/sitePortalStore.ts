import { defineStore } from 'pinia'

import { sitePortalService } from '@/services/sitePortalService'
import type { StatusReportFileInput } from '@/services/sitePortalService'
import type { EngineerProjectOption, StatusReport } from '@/types/StatusReport'

interface SitePortalState {
  projects: EngineerProjectOption[]
  todaysReport: StatusReport | null
  calendarReports: StatusReport[]
  isLoading: boolean
  error: string | undefined
}

export const useSitePortalStore = defineStore('sitePortal', {
  state: (): SitePortalState => ({
    projects: [],
    todaysReport: null,
    calendarReports: [],
    isLoading: false,
    error: undefined,
  }),

  actions: {
    async loadProjects() {
      this.projects = await sitePortalService.getMyProjects()
    },

    async loadTodaysReport() {
      this.todaysReport = await sitePortalService.getTodaysReport()
    },

    async fileTodaysReport(input: StatusReportFileInput) {
      const report = await sitePortalService.fileTodaysReport(input)
      this.todaysReport = report
      // Keep the calendar in sync if today happens to already be
      // showing in the currently-loaded range.
      this.calendarReports = [report, ...this.calendarReports.filter((r) => r.id !== report.id)]
      return report
    },

    async loadCalendarRange(start: string, end: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.calendarReports = await sitePortalService.getMyReports(start, end)
      } catch {
        this.error = 'Unable to load your report history. Please try again.'
      } finally {
        this.isLoading = false
      }
    },
  },
})
