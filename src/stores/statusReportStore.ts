import { defineStore } from 'pinia'

import { statusReportService } from '@/services/statusReportService'
import type { StatusReportAttachInput } from '@/services/statusReportService'
import type { StatusReport } from '@/types/StatusReport'

interface StatusReportInboxState {
  reports: StatusReport[]
  isLoading: boolean
  error: string | undefined
  // Separate from `reports` (the recipient's cross-project inbox queue)
  // -- this holds one project's full report history (Pending + Attached),
  // keyed by project number, for the read-only calendar on that
  // project's own Supervision > Documents tab.
  projectReports: Record<string, StatusReport[]>
  isProjectLoading: boolean
  projectError: string | undefined
  // One task's own attached report history -- see TaskFieldReportHistory.vue.
  // Only ever Attached reports (a report is only linked to a task once
  // reviewed and attached), keyed by task number.
  taskReports: Record<string, StatusReport[]>
  isTaskLoading: boolean
  taskError: string | undefined
}

export const useStatusReportStore = defineStore('statusReportInbox', {
  state: (): StatusReportInboxState => ({
    reports: [],
    isLoading: false,
    error: undefined,
    projectReports: {},
    isProjectLoading: false,
    projectError: undefined,
    taskReports: {},
    isTaskLoading: false,
    taskError: undefined,
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

    async loadForProject(projectNo: string) {
      this.isProjectLoading = true
      this.projectError = undefined
      try {
        this.projectReports = { ...this.projectReports, [projectNo]: await statusReportService.getForProject(projectNo) }
      } catch {
        this.projectError = 'Unable to load status reports for this project. Please try again.'
      } finally {
        this.isProjectLoading = false
      }
    },

    async loadForTask(taskNo: string) {
      this.isTaskLoading = true
      this.taskError = undefined
      try {
        this.taskReports = { ...this.taskReports, [taskNo]: await statusReportService.getForTask(taskNo) }
      } catch {
        this.taskError = 'Unable to load this task\'s report history. Please try again.'
      } finally {
        this.isTaskLoading = false
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
