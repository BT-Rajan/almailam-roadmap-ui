import { defineStore } from 'pinia'

import { approvalProcessService } from '@/services/approvalProcessService'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'
import { triggerBlobDownload } from '@/utils/fileDownload'

interface ProjectApprovalState {
  steps: ProjectApprovalStep[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
  isUploading: boolean
}

export const useProjectApprovalStore = defineStore('projectApproval', {
  state: (): ProjectApprovalState => ({
    steps: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
    isUploading: false,
  }),

  actions: {
    async loadSteps(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.steps = await approvalProcessService.getProjectSteps(projectId)
      } catch {
        this.error = 'Unable to load the approval process. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async uploadStageGateDocument(projectId: string, stageKey: string, file: File) {
      this.mutationError = undefined
      this.isUploading = true
      try {
        const updated = await approvalProcessService.uploadStageGateDocument(projectId, stageKey, file)
        this.steps = this.steps.map((s) => (s.stageKey === stageKey ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to upload stage gate document.'
      } finally {
        this.isUploading = false
      }
    },

    async downloadStageGateDocument(projectId: string, stageKey: string, filename: string) {
      this.mutationError = undefined
      try {
        const blob = await approvalProcessService.downloadStageGateDocument(projectId, stageKey)
        triggerBlobDownload(blob, filename)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to download stage gate document.'
      }
    },
  },
})
