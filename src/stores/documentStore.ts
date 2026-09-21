import { defineStore } from 'pinia'

import { documentService } from '@/services/documentService'
import { useProjectStore } from '@/stores/projectStore'
import type { DocumentStatus, DocumentType, DocumentVersion, DocumentViewMode, ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { CACHE_TTL_MS, getLoadGate } from '@/utils/loadGate'
import { replaceScope } from '@/utils/scopedCollection'
import { describeStoreError } from '@/utils/storeError'

interface DocumentPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface DocumentStoreState {
  documents: ProjectDocument[]
  // True only once loadDocuments() has fetched EVERY document -- `documents`
  // may also hold just some projects' rows (see loadDocumentsForProject), so
  // its length says nothing about completeness. See needsFullLoad.
  isFullyLoaded: boolean
  isFullLoading: boolean
  currentDocument: ProjectDocument | undefined
  currentVersions: DocumentVersion[]
  isLoading: boolean
  isDetailLoading: boolean
  error: string | undefined
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
    isFullyLoaded: false,
    isFullLoading: false,
    currentDocument: undefined,
    currentVersions: [],
    isLoading: false,
    isDetailLoading: false,
    error: undefined,
    searchTerm: '',
    typeFilter: 'All',
    statusFilter: 'All',
    viewMode: 'grid',
    pageItems: [],
    pagination: { page: 1, pageSize: 9, total: 0, totalPages: 1 },
    isPageLoading: false,
  }),

  getters: {
    // Whether a caller that needs every document should start a full load:
    // not already loaded, and not already being loaded.
    needsFullLoad(state): boolean {
      return !state.isFullyLoaded && !state.isFullLoading
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.typeFilter !== 'All' || state.statusFilter !== 'All'
    },

    // projectStore is the single, canonical place the full project list
    // lives -- see its own comment on `clients` for why this delegates
    // rather than keeping (and independently fetching) a second copy.
    projects(): Project[] {
      return useProjectStore().projects
    },

    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => useProjectStore().getProjectById(projectId)
    },

    documentsByProject(state) {
      return (projectId: string): ProjectDocument[] =>
        state.documents.filter((document) => document.projectId === projectId)
    },
  },

  actions: {
    async loadDocuments() {
      this.isLoading = true
      this.isFullLoading = true
      this.error = undefined
      try {
        const projectStore = useProjectStore()
        await Promise.all([
          documentService.getDocuments().then((documents) => {
            this.documents = documents
            this.isFullyLoaded = true
          }),
          projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
        ])
      } catch (error) {
        this.error = describeStoreError('Unable to load documents. Please try again.', error)
      } finally {
        this.isLoading = false
        this.isFullLoading = false
      }
    },

    // Loads just one project's documents, merging them into `documents` in
    // place of that project's old rows -- for views scoped to one project,
    // which shouldn't download every document in the company. Does NOT mark
    // the list fully loaded. A no-op when every document is already here,
    // unless `force`.
    async loadDocumentsForProject(projectId: string, options: { force?: boolean } = {}) {
      if (this.isFullyLoaded && !options.force) return
      await getLoadGate(this, `project:${projectId}`, CACHE_TTL_MS).run(async (isCurrent) => {
        this.isLoading = true
        this.error = undefined
        try {
          const projectDocuments = await documentService.getDocumentsByProject(projectId)
          if (isCurrent()) {
            this.documents = replaceScope(this.documents, projectDocuments, (document) => document.projectId === projectId)
          }
          return true
        } catch (error) {
          if (isCurrent()) this.error = describeStoreError('Unable to load documents. Please try again.', error)
          return false
        } finally {
          if (isCurrent()) this.isLoading = false
        }
      }, options)
    },

    // Fetches just the current page/filter/sort combination from the
    // server for the Documents browse table -- the actual pagination fix,
    // as opposed to loadDocuments() above which still loads everything
    // (safely, in bounded pages) for cross-reference lookups.
    async loadDocumentsPage() {
      this.isPageLoading = true
      this.error = undefined
      try {
        const projectStore = useProjectStore()
        if (projectStore.projects.length === 0) {
          await projectStore.loadProjects()
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
      } catch (error) {
        this.error = describeStoreError('Unable to load documents. Please try again.', error)
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
        const projectStore = useProjectStore()
        if (projectStore.projects.length === 0) {
          await projectStore.loadProjects()
        }
      } catch (error) {
        this.error = describeStoreError('Unable to load document. Please try again.', error)
      } finally {
        this.isDetailLoading = false
      }
    },

    async downloadCurrentDocument(): Promise<void> {
      if (!this.currentDocument) return
      const blob = await documentService.downloadDocument(this.currentDocument.id)
      triggerBlobDownload(blob, this.currentDocument.originalFilename ?? this.currentDocument.title)
    },

    async downloadVersion(versionId: string, filename: string): Promise<void> {
      if (!this.currentDocument) return
      const blob = await documentService.downloadVersion(this.currentDocument.id, versionId)
      triggerBlobDownload(blob, filename)
    },

    async setCurrentDocumentStatus(status: DocumentStatus, reason?: string): Promise<void> {
      if (!this.currentDocument) return
      const updated = await documentService.setDocumentStatus(this.currentDocument.id, status, reason)
      this.currentDocument = updated
      this.documents = this.documents.map((doc) => (doc.id === updated.id ? updated : doc))
    },

    async addCurrentDocumentVersion(file: File, notes?: string): Promise<void> {
      if (!this.currentDocument) return
      await documentService.addVersion(this.currentDocument.id, file, notes)
      // The document's own revision/upload metadata changes too (new
      // current revision, new uploader/date), not just its version list.
      const [document, versions] = await Promise.all([
        documentService.getDocumentById(this.currentDocument.id),
        documentService.getDocumentVersions(this.currentDocument.id),
      ])
      if (document) {
        this.currentDocument = document
        this.documents = this.documents.map((doc) => (doc.id === document.id ? document : doc))
      }
      this.currentVersions = versions
    },

    async deleteCurrentDocument(): Promise<void> {
      if (!this.currentDocument) return
      await documentService.deleteDocument(this.currentDocument.id)
      this.documents = this.documents.filter((doc) => doc.id !== this.currentDocument?.id)
      this.currentDocument = undefined
    },

    addDocument(document: ProjectDocument) {
      this.documents = [document, ...this.documents]
    },

    // Persists an uploaded document via the backend API.
    async uploadDocument(
      file: File | undefined,
      projectId: string,
      title: string,
      type: DocumentType,
      externalLink?: string,
    ): Promise<ProjectDocument> {
      const document = await documentService.uploadDocument(file, projectId, title, type, externalLink)
      this.documents = [document, ...this.documents]
      return document
    },

    async updateDocument(
      documentId: string,
      title: string,
      externalLink?: string | null,
      uploadDate?: string,
    ): Promise<ProjectDocument> {
      const updated = await documentService.updateDocument(documentId, title, externalLink, uploadDate)
      this.documents = this.documents.map((document) => (document.id === documentId ? updated : document))
      if (this.currentDocument?.id === documentId) {
        this.currentDocument = updated
      }
      return updated
    },

    // Attaches/replaces a design document's uploaded file (via the
    // existing version-upload endpoint, same as VersionHistory's "new
    // revision" -- a design row can start link-only and gain a file
    // later, same mechanism either way) and folds the result back into
    // the local list without requiring currentDocument to be set.
    async attachFile(documentId: string, file: File): Promise<ProjectDocument | undefined> {
      await documentService.addVersion(documentId, file)
      const document = await documentService.getDocumentById(documentId)
      if (document) {
        this.documents = this.documents.map((d) => (d.id === documentId ? document : d))
        if (this.currentDocument?.id === documentId) {
          this.currentDocument = document
        }
      }
      return document
    },

    async deleteDocument(documentId: string): Promise<void> {
      await documentService.deleteDocument(documentId)
      this.documents = this.documents.filter((document) => document.id !== documentId)
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
