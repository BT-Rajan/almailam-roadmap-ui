import { defineStore } from 'pinia'

import { knowledgeService } from '@/services/knowledgeService'
import type { KnowledgeDocument, KnowledgeQAEntry } from '@/types/Knowledge'

interface KnowledgeStoreState {
  documents: KnowledgeDocument[]
  history: KnowledgeQAEntry[]
  // undefined until loaded -- distinct from `false`, so the sparkle icon
  // and ask panels can stay hidden/quiet rather than briefly flashing
  // "disabled" before the real status is known.
  isEnabled: boolean | undefined
  isDrawerOpen: boolean
  isLoading: boolean
  isUploading: boolean
  isAsking: boolean
  error: string | undefined
  askError: string | undefined
}

export const useKnowledgeStore = defineStore('knowledge', {
  state: (): KnowledgeStoreState => ({
    documents: [],
    history: [],
    isEnabled: undefined,
    isDrawerOpen: false,
    isLoading: false,
    isUploading: false,
    isAsking: false,
    error: undefined,
    askError: undefined,
  }),

  getters: {
    activeDocuments(state): KnowledgeDocument[] {
      return state.documents.filter((document) => document.isActive)
    },
  },

  actions: {
    async loadStatus() {
      try {
        const status = await knowledgeService.getStatus()
        this.isEnabled = status.isEnabled
      } catch {
        // Leave isEnabled undefined -- the sparkle icon/ask panels stay
        // hidden rather than guessing, same principle as every other
        // honest-unavailability path in this feature.
      }
    },

    openDrawer() {
      this.isDrawerOpen = true
    },

    closeDrawer() {
      this.isDrawerOpen = false
    },

    toggleDrawer() {
      this.isDrawerOpen = !this.isDrawerOpen
    },

    async loadDocuments() {
      this.isLoading = true
      this.error = undefined
      try {
        this.documents = await knowledgeService.getDocuments()
      } catch {
        this.error = 'Unable to load knowledgebase documents. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async uploadDocument(file: File, title: string): Promise<KnowledgeDocument> {
      this.isUploading = true
      try {
        const document = await knowledgeService.uploadDocument(file, title)
        this.documents = [document, ...this.documents]
        return document
      } finally {
        this.isUploading = false
      }
    },

    async setDocumentActive(documentId: string, isActive: boolean): Promise<void> {
      const updated = await knowledgeService.setActive(documentId, isActive)
      this.documents = this.documents.map((document) => (document.id === documentId ? updated : document))
    },

    async deleteDocument(documentId: string): Promise<void> {
      await knowledgeService.deleteDocument(documentId)
      this.documents = this.documents.filter((document) => document.id !== documentId)
    },

    async ask(question: string, documentId?: string): Promise<void> {
      this.isAsking = true
      this.askError = undefined
      try {
        const result = await knowledgeService.ask(question, documentId)
        this.history = [
          {
            id: `${Date.now()}`,
            question,
            askedAt: new Date().toISOString(),
            ...result,
          },
          ...this.history,
        ]
      } catch (error) {
        this.askError = error instanceof Error && error.message ? error.message : 'Unable to get an answer. Please try again.'
      } finally {
        this.isAsking = false
      }
    },

    clearHistory() {
      this.history = []
    },
  },
})
