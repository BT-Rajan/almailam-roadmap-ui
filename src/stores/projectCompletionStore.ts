import { defineStore } from 'pinia'

import { projectService } from '@/services/projectService'
import type { ProjectCompletionChecklist, ProjectCompletionSummary } from '@/types/ProjectCompletion'

interface ProjectCompletionState {
  summary: ProjectCompletionSummary | undefined
  checklist: ProjectCompletionChecklist | undefined
  isLoading: boolean
  error: string | undefined
  isSaving: boolean
  saveError: string | undefined
}

export const useProjectCompletionStore = defineStore('projectCompletion', {
  state: (): ProjectCompletionState => ({
    summary: undefined,
    checklist: undefined,
    isLoading: false,
    error: undefined,
    isSaving: false,
    saveError: undefined,
  }),

  actions: {
    async loadSummary(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        const [summary, checklist] = await Promise.all([
          projectService.getCompletionSummary(projectId),
          projectService.getCompletionChecklist(projectId),
        ])
        this.summary = summary
        this.checklist = checklist
      } catch {
        this.error = 'Unable to load the project summary. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async saveNotes(projectId: string, notes: string) {
      this.isSaving = true
      this.saveError = undefined
      try {
        this.summary = await projectService.updateCompletionNotes(projectId, notes)
      } catch (error) {
        this.saveError = error instanceof Error ? error.message : 'Failed to save notes.'
      } finally {
        this.isSaving = false
      }
    },

    async saveDeviationNotes(projectId: string, notes: string) {
      this.isSaving = true
      this.saveError = undefined
      try {
        this.summary = await projectService.updateDeviationNotes(projectId, notes)
      } catch (error) {
        this.saveError = error instanceof Error ? error.message : 'Failed to save deviation notes.'
      } finally {
        this.isSaving = false
      }
    },
  },
})
