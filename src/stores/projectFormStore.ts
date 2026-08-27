import { defineStore } from 'pinia'

import { projectFormService } from '@/services/projectFormService'
import type { ProjectFormEntry, ProjectFormEntryStatus } from '@/types/Government'

interface ProjectFormState {
  entries: ProjectFormEntry[]
  isLoading: boolean
  error: string | undefined
  mutationError: string | undefined
}

// Approvals & Permits' own filed-form records for one project at a
// time -- loaded fresh whenever ProjectGovernmentTab.vue mounts, same
// "one project in view at once" convention as projectStageStore.
export const useProjectFormStore = defineStore('projectForm', {
  state: (): ProjectFormState => ({
    entries: [],
    isLoading: false,
    error: undefined,
    mutationError: undefined,
  }),

  getters: {
    entriesByAuthority: (state) => (authorityId: string) =>
      state.entries.filter((entry) => entry.authorityId === authorityId),
  },

  actions: {
    async load(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.entries = await projectFormService.getEntries(projectId)
      } catch {
        this.error = 'Unable to load filed forms. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async createEntry(projectId: string, formId: string, fieldValues: Record<string, string>) {
      this.mutationError = undefined
      try {
        const entry = await projectFormService.createEntry(projectId, formId, fieldValues)
        this.entries = [...this.entries, entry]
        return entry
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to save the form.'
        return undefined
      }
    },

    async updateEntry(projectId: string, entryId: string, fieldValues: Record<string, string>) {
      this.mutationError = undefined
      try {
        const entry = await projectFormService.updateEntry(projectId, entryId, fieldValues)
        this.entries = this.entries.map((e) => (e.id === entryId ? entry : e))
        return entry
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to save the form.'
        return undefined
      }
    },

    async setEntryStatus(projectId: string, entryId: string, status: ProjectFormEntryStatus) {
      this.mutationError = undefined
      try {
        const entry = await projectFormService.setEntryStatus(projectId, entryId, status)
        this.entries = this.entries.map((e) => (e.id === entryId ? entry : e))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to change status.'
      }
    },

    async deleteEntry(projectId: string, entryId: string) {
      this.mutationError = undefined
      try {
        await projectFormService.deleteEntry(projectId, entryId)
        this.entries = this.entries.filter((e) => e.id !== entryId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Failed to remove the form.'
      }
    },
  },
})
