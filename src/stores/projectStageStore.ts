import { defineStore } from 'pinia'

import { approvalProcessService } from '@/services/approvalProcessService'
import { executionStepService } from '@/services/executionStepService'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'
import type { ProjectExecutionStep } from '@/types/ExecutionStep'
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
    // The weightPercentage-weighted sum of every execution activity's own
    // completion percentage -- mirrors the server's own project.progress
    // computation (execution_step_service._recompute_progress) so the UI
    // can show a live number while an activity is being edited, before
    // the project record itself has been refreshed.
    weightedProgress(state): number {
      const total = state.executionSteps.reduce(
        (sum, step) => sum + (step.weightPercentage * step.completionPercentage) / 100,
        0,
      )
      return Math.max(0, Math.min(100, Math.round(total)))
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
