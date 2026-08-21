import { defineStore } from 'pinia'

import { approvalProcessService } from '@/services/approvalProcessService'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'

interface ProjectApprovalState {
  steps: ProjectApprovalStep[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
}

export const useProjectApprovalStore = defineStore('projectApproval', {
  state: (): ProjectApprovalState => ({
    steps: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
  }),

  getters: {
    nextActionableStepId(state): string | undefined {
      return [...state.steps].sort((a, b) => a.sequenceNumber - b.sequenceNumber).find((s) => s.status === 'Pending')?.id
    },
    lastResolvedStepId(state): string | undefined {
      const resolved = state.steps.filter((s) => s.status !== 'Pending')
      if (resolved.length === 0) return undefined
      return resolved.reduce((latest, s) => (s.sequenceNumber > latest.sequenceNumber ? s : latest)).id
    },
  },

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

    async completeStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await approvalProcessService.completeStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to complete step.'
      }
    },

    async uncompleteStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await approvalProcessService.uncompleteStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to undo step.'
      }
    },

    async waiveStep(projectId: string, stepId: string, reason: string) {
      this.mutationError = undefined
      try {
        const updated = await approvalProcessService.waiveStep(projectId, stepId, reason)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to waive step.'
      }
    },

    async unwaiveStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await approvalProcessService.unwaiveStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to undo waive.'
      }
    },
  },
})
