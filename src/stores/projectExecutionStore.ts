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
    // The weightPercentage-weighted sum of every step's own completion
    // percentage -- mirrors the server's own project.progress
    // computation (execution_step_service._recompute_progress) so the
    // UI can show a live number while a step is being edited, before
    // the project record itself has been refreshed.
    weightedProgress(state): number {
      const total = state.steps.reduce(
        (sum, step) => sum + (step.weightPercentage * step.completionPercentage) / 100,
        0,
      )
      return Math.max(0, Math.min(100, Math.round(total)))
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

    async setStepProgress(projectId: string, stepId: string, completionPercentage: number, remarks: string | null) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.setStepProgress(projectId, stepId, completionPercentage, remarks)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to update step progress.'
      }
    },
  },
})
