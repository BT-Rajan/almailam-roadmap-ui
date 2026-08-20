import { defineStore } from 'pinia'

import { sitePortalService } from '@/services/sitePortalService'
import type { StatusReportFileInput } from '@/services/sitePortalService'
import type { EngineerProjectOption, StatusReport } from '@/types/StatusReport'

interface SitePortalState {
  projects: EngineerProjectOption[]
  // One entry per project the engineer has already filed today, not a
  // single report -- an engineer on several projects files a separate
  // report per project each day. Keyed by projectId for O(1) lookup
  // from the report form ("has today's report for this project
  // already been filed, and if so, what does it say").
  todaysReports: Record<string, StatusReport>
  calendarReports: StatusReport[]
  isLoading: boolean
  error: string | undefined
}

export const useSitePortalStore = defineStore('sitePortal', {
  state: (): SitePortalState => ({
    projects: [],
    todaysReports: {},
    calendarReports: [],
    isLoading: false,
    error: undefined,
  }),

  actions: {
    async loadProjects() {
      this.projects = await sitePortalService.getMyProjects()
    },

    async loadTodaysReports() {
      const reports = await sitePortalService.getTodaysReports()
      this.todaysReports = Object.fromEntries(reports.map((r) => [r.projectId, r]))
    },

    async fileTodaysReport(input: StatusReportFileInput) {
      const report = await sitePortalService.fileTodaysReport(input)
      this.todaysReports = { ...this.todaysReports, [report.projectId]: report }
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
