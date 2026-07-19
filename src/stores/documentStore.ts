import { defineStore } from 'pinia'

import { documentService } from '@/services/documentService'
import { projectService } from '@/services/projectService'
import type { DocumentStatus, DocumentType, DocumentVersion, DocumentViewMode, ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'

interface DocumentStoreState {
  documents: ProjectDocument[]
  projects: Project[]
  currentDocument: ProjectDocument | undefined
  currentVersions: DocumentVersion[]
  isLoading: boolean
  isDetailLoading: boolean
  error: string | undefined
  searchTerm: string
  typeFilter: DocumentType | 'All'
  statusFilter: DocumentStatus | 'All'
  viewMode: DocumentViewMode
}

export const useDocumentStore = defineStore('document', {
  state: (): DocumentStoreState => ({
    documents: [],
    projects: [],
    currentDocument: undefined,
    currentVersions: [],
    isLoading: false,
    isDetailLoading: false,
    error: undefined,
    searchTerm: '',
    typeFilter: 'All',
    statusFilter: 'All',
    viewMode: 'grid',
  }),

  getters: {
    filteredDocuments(state): ProjectDocument[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.documents.filter((document) => {
        const matchesSearch =
          term.length === 0 ||
          document.title.toLowerCase().includes(term) ||
          document.uploadedBy.toLowerCase().includes(term)

        const matchesType = state.typeFilter === 'All' || document.type === state.typeFilter
        const matchesStatus = state.statusFilter === 'All' || document.status === state.statusFilter

        return matchesSearch && matchesType && matchesStatus
      })
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.typeFilter !== 'All' || state.statusFilter !== 'All'
    },

    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },
  },

  actions: {
    async loadDocuments() {
      this.isLoading = true
      this.error = undefined
      try {
        const [documents, projects] = await Promise.all([documentService.getDocuments(), projectService.getProjects()])
        this.documents = documents
        this.projects = projects
      } catch {
        this.error = 'Unable to load documents. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async loadDocumentDetail(documentId: string) {
      this.isDetailLoading = true
      this.error = undefined
      try {
        const [document, versions] = await Promise.all([
          documentService.getDocumentById(documentId),
          documentService.getDocumentVersions(documentId),
        ])
        this.currentDocument = document
        this.currentVersions = versions
        if (this.projects.length === 0) {
          this.projects = await projectService.getProjects()
        }
      } catch {
        this.error = 'Unable to load document. Please try again.'
      } finally {
        this.isDetailLoading = false
      }
    },

    addDocument(document: ProjectDocument) {
      this.documents = [document, ...this.documents]
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setTypeFilter(type: DocumentType | 'All') {
      this.typeFilter = type
    },

    setStatusFilter(status: DocumentStatus | 'All') {
      this.statusFilter = status
    },

    setViewMode(mode: DocumentViewMode) {
      this.viewMode = mode
    },

    clearFilters() {
      this.searchTerm = ''
      this.typeFilter = 'All'
      this.statusFilter = 'All'
    },
  },
})
