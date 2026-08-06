import { defineStore } from 'pinia'

import { aiService } from '@/services/aiService'
import { documentService } from '@/services/documentService'
import { projectService } from '@/services/projectService'
import type { DocumentStatus, DocumentType, DocumentVersion, DocumentViewMode, ProjectDocument } from '@/types/Document'
import type { DocumentAIReview } from '@/types/AiReview'
import type { Project } from '@/types/Project'

interface DocumentPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface DocumentStoreState {
  documents: ProjectDocument[]
  projects: Project[]
  currentDocument: ProjectDocument | undefined
  currentVersions: DocumentVersion[]
  currentReview: DocumentAIReview | undefined
  isLoading: boolean
  isDetailLoading: boolean
  isReviewLoading: boolean
  error: string | undefined
  reviewError: string | undefined
  searchTerm: string
  typeFilter: DocumentType | 'All'
  statusFilter: DocumentStatus | 'All'
  viewMode: DocumentViewMode
  // Server-paginated browse state for DocumentsPage -- separate from
  // `documents` above, which stays a full, unpaginated cache because other
  // pages (e.g. a project's Documents tab) filter it locally by project id.
  pageItems: ProjectDocument[]
  pagination: DocumentPaginationState
  isPageLoading: boolean
}

export const useDocumentStore = defineStore('document', {
  state: (): DocumentStoreState => ({
    documents: [],
    projects: [],
    currentDocument: undefined,
    currentVersions: [],
    currentReview: undefined,
    isLoading: false,
    isDetailLoading: false,
    isReviewLoading: false,
    error: undefined,
    reviewError: undefined,
    searchTerm: '',
    typeFilter: 'All',
    statusFilter: 'All',
    viewMode: 'grid',
    pageItems: [],
    pagination: { page: 1, pageSize: 9, total: 0, totalPages: 1 },
    isPageLoading: false,
  }),

  getters: {
    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.typeFilter !== 'All' || state.statusFilter !== 'All'
    },

    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },

    documentsByProject(state) {
      return (projectId: string): ProjectDocument[] =>
        state.documents.filter((document) => document.projectId === projectId)
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

    // Fetches just the current page/filter/sort combination from the
    // server for the Documents browse table -- the actual pagination fix,
    // as opposed to loadDocuments() above which still loads everything
    // (safely, in bounded pages) for cross-reference lookups.
    async loadDocumentsPage() {
      this.isPageLoading = true
      this.error = undefined
      try {
        if (this.projects.length === 0) {
          this.projects = await projectService.getProjects()
        }
        const result = await documentService.getDocumentsPage({
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          search: this.searchTerm.trim() || undefined,
          type: this.typeFilter !== 'All' ? this.typeFilter : undefined,
          status: this.statusFilter !== 'All' ? this.statusFilter : undefined,
        })
        this.pageItems = result.items
        this.pagination = {
          page: result.page,
          pageSize: result.pageSize,
          total: result.total,
          totalPages: result.totalPages,
        }
      } catch {
        this.error = 'Unable to load documents. Please try again.'
      } finally {
        this.isPageLoading = false
      }
    },

    setPage(page: number) {
      this.pagination.page = page
      void this.loadDocumentsPage()
    },

    setPageSize(size: number) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      void this.loadDocumentsPage()
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

    async loadDocumentReview(documentId: string) {
      this.isReviewLoading = true
      this.reviewError = undefined
      try {
        this.currentReview = await aiService.getDocumentReview(documentId)
      } catch {
        this.reviewError = 'AI service is currently unavailable. Please try again later.'
      } finally {
        this.isReviewLoading = false
      }
    },

    addDocument(document: ProjectDocument) {
      this.documents = [document, ...this.documents]
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    // Called from the search box's debounced @search event, once the
    // person has paused typing, so we're not firing a request per keystroke.
    applySearch(term: string) {
      this.searchTerm = term
      this.pagination.page = 1
      void this.loadDocumentsPage()
    },

    setTypeFilter(type: DocumentType | 'All') {
      this.typeFilter = type
      this.pagination.page = 1
      void this.loadDocumentsPage()
    },

    setStatusFilter(status: DocumentStatus | 'All') {
      this.statusFilter = status
      this.pagination.page = 1
      void this.loadDocumentsPage()
    },

    setViewMode(mode: DocumentViewMode) {
      this.viewMode = mode
    },

    clearFilters() {
      this.searchTerm = ''
      this.typeFilter = 'All'
      this.statusFilter = 'All'
      this.pagination.page = 1
      void this.loadDocumentsPage()
    },
  },
})
