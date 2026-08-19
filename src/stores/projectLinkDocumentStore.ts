import { defineStore } from 'pinia'

import { projectLinkDocumentService } from '@/services/projectLinkDocumentService'
import type { ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'

interface ProjectLinkDocumentStoreState {
  // Keyed by projectId so switching between projects' Documents tabs
  // doesn't require refetching every time, and one project's list can't
  // bleed into another's.
  byProject: Record<string, ProjectLinkDocument[]>
  isLoading: boolean
  error: string | undefined
}

export const useProjectLinkDocumentStore = defineStore('projectLinkDocument', {
  state: (): ProjectLinkDocumentStoreState => ({
    byProject: {},
    isLoading: false,
    error: undefined,
  }),

  getters: {
    documentsFor(state) {
      return (projectId: string): ProjectLinkDocument[] => state.byProject[projectId] ?? []
    },
    documentsForCategory(state) {
      return (projectId: string, category: ProjectLinkDocumentCategory): ProjectLinkDocument[] =>
        (state.byProject[projectId] ?? []).filter((document) => document.category === category)
    },
  },

  actions: {
    async loadForProject(projectId: string): Promise<void> {
      this.isLoading = true
      this.error = undefined
      try {
        this.byProject[projectId] = await projectLinkDocumentService.getLinkDocumentsForProject(projectId)
      } catch {
        this.error = 'Unable to load documents. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async addDocument(
      projectId: string,
      category: ProjectLinkDocumentCategory,
      name: string,
      path: string,
    ): Promise<ProjectLinkDocument> {
      const document = await projectLinkDocumentService.createLinkDocument(projectId, category, name, path)
      this.byProject[projectId] = [document, ...(this.byProject[projectId] ?? [])]
      return document
    },

    async deleteDocument(projectId: string, linkDocumentId: string): Promise<void> {
      await projectLinkDocumentService.deleteLinkDocument(projectId, linkDocumentId)
      this.byProject[projectId] = (this.byProject[projectId] ?? []).filter(
        (document) => document.id !== linkDocumentId,
      )
    },
  },
})
