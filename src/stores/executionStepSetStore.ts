import { defineStore } from 'pinia'

import { executionStepService } from '@/services/executionStepService'
import type { ExecutionStepSet } from '@/types/ExecutionStep'

interface ExecutionStepSetState {
  stepSets: ExecutionStepSet[]
  selectedStepSetId: string | undefined
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
}

// The admin-managed list of named step sets (see execution_step_
// service.py's ExecutionStepSetTemplate) -- separate from
// executionStepTemplateStore, which manages the steps *within*
// whichever one set is currently selected here.
export const useExecutionStepSetStore = defineStore('executionStepSet', {
  state: (): ExecutionStepSetState => ({
    stepSets: [],
    selectedStepSetId: undefined,
    isLoading: false,
    error: undefined,
    mutationError: undefined,
  }),

  actions: {
    async loadStepSets() {
      this.isLoading = true
      this.error = undefined
      try {
        this.stepSets = await executionStepService.getStepSets()
        if (this.selectedStepSetId === undefined || !this.stepSets.some((s) => s.id === this.selectedStepSetId)) {
          this.selectedStepSetId = this.stepSets[0]?.id
        }
      } catch {
        this.error = 'Unable to load execution step sets. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectStepSet(stepSetId: string) {
      this.selectedStepSetId = stepSetId
    },

    async createStepSet(name: string, description: string | null) {
      this.mutationError = undefined
      try {
        const stepSet = await executionStepService.createStepSet(name, description)
        this.stepSets = [...this.stepSets, stepSet]
        this.selectedStepSetId = stepSet.id
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to add step set.'
      }
    },

    async updateStepSet(stepSetId: string, fields: { name?: string; description?: string | null }) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.updateStepSet(stepSetId, fields)
        this.stepSets = this.stepSets.map((s) => (s.id === stepSetId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to update step set.'
      }
    },

    async deleteStepSet(stepSetId: string) {
      this.mutationError = undefined
      try {
        await executionStepService.deleteStepSet(stepSetId)
        this.stepSets = this.stepSets.filter((s) => s.id !== stepSetId)
        if (this.selectedStepSetId === stepSetId) this.selectedStepSetId = this.stepSets[0]?.id
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to remove step set.'
      }
    },
  },
})
