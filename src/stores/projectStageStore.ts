import { defineStore } from 'pinia'

import { approvalProcessService } from '@/services/approvalProcessService'
import { executionStepService } from '@/services/executionStepService'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'
import type { ExecutionStepBulkItem, ProjectExecutionStep } from '@/types/ExecutionStep'
import { triggerBlobDownload } from '@/utils/fileDownload'

// Replaces projectApprovalStore + projectExecutionStore. The 5 approval
// stages and the 23 execution activities are two independent tracks that
// both run against the same project at the same time -- neither gates
// the other (a stage gate document can be uploaded whether or not any
// particular execution activity is done). They used to be fetched from
// two separate stores and reconciled by stageKey inside
// ProjectProcessTab.vue; that reconciliation is gone because the
// activities were never actually partitioned one-to-one under a single
// stage to begin with. This store still makes two API calls (the two
// resources remain genuinely different -- a checklist vs. a gate
// document -- so splitting the tables wasn't the fix) but loads them
// together and exposes one interface, so the component consuming this
// no longer has to know there are two backends behind it.
interface ProjectStageState {
  approvalSteps: ProjectApprovalStep[]
  executionSteps: ProjectExecutionStep[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
  isUploading: boolean
}

export const useProjectStageStore = defineStore('projectStage', {
  state: (): ProjectStageState => ({
    approvalSteps: [],
    executionSteps: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
    isUploading: false,
  }),

  getters: {
    // Excludes activities this project has marked not applicable --
    // mirrors execution_step_service.included_steps.
    includedExecutionSteps(state): ProjectExecutionStep[] {
      return state.executionSteps.filter((s) => !s.isExcluded)
    },

    // The weightPercentage-weighted sum of every INCLUDED execution
    // activity's own completion percentage, renormalized against the
    // included weight total -- mirrors the server's own project.progress
    // computation (execution_step_service._recompute_progress) so the UI
    // can show a live number while an activity is being edited, before
    // the project record itself has been refreshed.
    weightedProgress(): number {
      const steps = this.includedExecutionSteps as ProjectExecutionStep[]
      const totalWeight = steps.reduce((sum, step) => sum + step.weightPercentage, 0)
      if (totalWeight <= 0) return 0
      const weighted = steps.reduce((sum, step) => sum + (step.weightPercentage * step.completionPercentage) / 100, 0)
      return Math.max(0, Math.min(100, Math.round((weighted / totalWeight) * 100)))
    },

    stageGateCompleteCount(state): number {
      return state.approvalSteps.filter((s) => s.isComplete).length
    },

    // Flat, sequence-ordered -- activities are not grouped under a stage.
    orderedExecutionSteps(state): ProjectExecutionStep[] {
      return [...state.executionSteps].sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    },
  },

  actions: {
    async load(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        const [approvalSteps, executionSteps] = await Promise.all([
          approvalProcessService.getProjectSteps(projectId),
          executionStepService.getProjectSteps(projectId),
        ])
        this.approvalSteps = approvalSteps
        this.executionSteps = executionSteps
      } catch {
        this.error = 'Unable to load the project process. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async setStepProgress(projectId: string, stepId: string, completionPercentage: number, remarks: string | null) {
      this.mutationError = undefined
      try {
        const updated = await executionStepService.setStepProgress(projectId, stepId, completionPercentage, remarks)
        this.executionSteps = this.executionSteps.map((s) => (s.id === stepId ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to update activity progress.'
      }
    },

    // The checklist's single Save button -- every changed activity
    // (progress, remarks, excluded/reason) lands in one request.
    async bulkSaveSteps(projectId: string, items: ExecutionStepBulkItem[]) {
      this.mutationError = undefined
      try {
        this.executionSteps = await executionStepService.bulkSaveProjectSteps(projectId, items)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to save checklist.'
      }
    },

    // Staff's own "freedom to add" beyond whatever the project's
    // assigned step set specified -- the complement of excluding a
    // template-derived step (the "reduce" half of the same freedom).
    async addCustomStep(projectId: string, name: string, weightPercentage: number, stageKey: string) {
      this.mutationError = undefined
      try {
        const step = await executionStepService.addCustomProjectStep(projectId, name, weightPercentage, stageKey)
        this.executionSteps = [...this.executionSteps, step]
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to add step.'
      }
    },

    async deleteCustomStep(projectId: string, stepId: string) {
      this.mutationError = undefined
      try {
        await executionStepService.deleteCustomProjectStep(projectId, stepId)
        this.executionSteps = this.executionSteps.filter((s) => s.id !== stepId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to remove step.'
      }
    },

    async uploadStageGateDocument(projectId: string, stageKey: string, file: File) {
      this.mutationError = undefined
      this.isUploading = true
      try {
        const updated = await approvalProcessService.uploadStageGateDocument(projectId, stageKey, file)
        this.approvalSteps = this.approvalSteps.map((s) => (s.stageKey === stageKey ? updated : s))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to upload stage gate document.'
      } finally {
        this.isUploading = false
      }
    },

    // Second, independent path to close a stage gate: confirming
    // completion once the documents tagged to this stage (Documents
    // tab, ProjectDocument.stageKey) have been reviewed -- no file
    // involved, unlike uploadStageGateDocument above.
    async completeStageFromDocuments(projectId: string, stageKey: string) {
      this.mutationError = undefined
      try {
        const updated = await approvalProcessService.completeStageFromDocuments(projectId, stageKey)
        this.approvalSteps = this.approvalSteps.map((s) => (s.stageKey === stageKey ? updated : s))
        return updated
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to mark stage complete.'
        return undefined
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
