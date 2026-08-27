import { defineStore } from 'pinia'

import { executionStepService } from '@/services/executionStepService'
import type { ExecutionStepTemplateItem } from '@/types/ExecutionStep'

interface ExecutionStepTemplateState {
  stepSetId: string | undefined
  steps: ExecutionStepTemplateItem[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
}

// The steps within ONE step set -- which set is scoped by loadTemplate's
// stepSetId argument (see AdminExecutionStepsPage.vue, which drives this
// from executionStepSetStore's currently selected set).
export const useExecutionStepTemplateStore = defineStore('executionStepTemplate', {
  state: (): ExecutionStepTemplateState => ({
    stepSetId: undefined,
    steps: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
  }),

  getters: {
    // Admin needs to see at a glance whether the weights actually add up
    // to something sensible -- nothing stops them from leaving it under-
    // or over-100 while mid-edit, but it should be obvious when that's
    // the case rather than only showing up as a confusing progress
    // number later on a real project.
    totalWeight(state): number {
      return Math.round(state.steps.reduce((sum, s) => sum + s.weightPercentage, 0) * 100) / 100
    },
  },

  actions: {
    async loadTemplate(stepSetId: string) {
      this.stepSetId = stepSetId
      this.isLoading = true
      this.error = undefined
      try {
        this.steps = await executionStepService.getTemplate(stepSetId)
      } catch {
        this.error = 'Unable to load the execution step template. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async createStep(name: string, weightPercentage: number, stageKey: string, isOptional: boolean, triggerKey: string) {
      if (!this.stepSetId) return
      this.mutationError = undefined
      try {
        const step = await executionStepService.createTemplateStep(
          this.stepSetId, name, weightPercentage, stageKey, isOptional, triggerKey,
        )
        this.steps = [...this.steps, step]
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to add step.'
      }
    },

    async updateStep(
      stepId: string,
      fields: { name?: string; weightPercentage?: number; stageKey?: string; isOptional?: boolean; triggerKey?: string },
    ) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.updateTemplateStep(stepId, fields)
        this.steps = this.steps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to update step.'
      }
    },

    async deleteStep(stepId: string) {
      this.mutationError = undefined
      try {
        await executionStepService.deleteTemplateStep(stepId)
        if (this.stepSetId) await this.loadTemplate(this.stepSetId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to remove step.'
      }
    },

    async moveStep(stepId: string, direction: 'up' | 'down') {
      this.mutationError = undefined
      try {
        this.steps = await executionStepService.moveTemplateStep(stepId, direction)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to reorder step.'
      }
    },
  },
})
