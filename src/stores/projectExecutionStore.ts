import { defineStore } from 'pinia'

import { executionStepService } from '@/services/executionStepService'
import type { ProjectExecutionStep } from '@/types/ExecutionStep'

interface ProjectExecutionState {
  steps: ProjectExecutionStep[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
}

export const useProjectExecutionStore = defineStore('projectExecution', {
  state: (): ProjectExecutionState => ({
    steps: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
  }),

  getters: {
    // The one step the UI should actually offer to complete or waive
    // right now -- the first Pending one in sequence. Every other
    // Pending step is genuinely not actionable yet (linear order,
    // enforced by the backend too), so the UI shouldn't pretend
    // otherwise by showing an enabled button for a step that would
    // just get rejected.
    nextActionableStepId(state): string | undefined {
      return [...state.steps].sort((a, b) => a.sequenceNumber - b.sequenceNumber).find((s) => s.status === 'Pending')?.id
    },
    // The only step eligible to be undone -- the most recently
    // resolved (Completed or Waived) one by sequence order, mirroring
    // the backend's own rule exactly.
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
        this.steps = await executionStepService.getProjectSteps(projectId)
      } catch {
        this.error = 'Unable to load the execution checklist. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async completeStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.completeStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to complete step.'
      }
    },

    async uncompleteStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.uncompleteStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to undo step.'
      }
    },

    async waiveStep(projectId: string, stepId: string, reason: string) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.waiveStep(projectId, stepId, reason)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to waive step.'
      }
    },

    async unwaiveStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.unwaiveStep(projectId, stepId)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to undo waive.'
      }
    },
  },
})
