import { defineStore } from 'pinia'

import { projectService } from '@/services/projectService'
import type { ProjectCreateInput, ProjectUpdateInput } from '@/services/projectService'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import type { Client } from '@/types/Client'
import type { AddServicesInput, Project, ProjectPriority, ProjectStatus, ProjectViewMode, WorkflowStage } from '@/types/Project'

interface ProjectPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface ProjectStoreState {
  projects: Project[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  statusFilter: ProjectStatus | 'All'
  stageFilter: WorkflowStage | 'All'
  priorityFilter: ProjectPriority | 'All'
  myProjectsOnly: boolean
  viewMode: ProjectViewMode
  // Browses soft-deleted projects (see restoreProject) instead of active
  // ones -- an alternate view of the same paginated table, not combined
  // with the filters above.
  showDeleted: boolean
  // Server-paginated browse state for ProjectsPage -- separate from
  // `projects` above, which stays a full, unpaginated cache because other
  // pages (e.g. the project workspace) look a project up locally by id
  // rather than fetching it individually.
  pageItems: Project[]
  pagination: ProjectPaginationState
  isPageLoading: boolean
}

export const useProjectStore = defineStore('project', {
  state: (): ProjectStoreState => ({
    projects: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    statusFilter: 'All',
    stageFilter: 'All',
    priorityFilter: 'All',
    myProjectsOnly: false,
    viewMode: 'grid',
    showDeleted: false,
    pageItems: [],
    pagination: { page: 1, pageSize: 9, total: 0, totalPages: 1 },
    isPageLoading: false,
  }),

  getters: {
    hasActiveFilters(state): boolean {
      return (
        state.searchTerm.trim().length > 0 ||
        state.statusFilter !== 'All' ||
        state.stageFilter !== 'All' ||
        state.priorityFilter !== 'All' ||
        state.myProjectsOnly
      )
    },

    // clientStore is the single, canonical place the full client list
    // lives -- this used to be a second, independently-fetched copy of
    // the exact same data (loadProjects/loadProjectsPage both called
    // clientService.getClients() themselves). Delegating keeps every
    // existing `projectStore.clients` / `projectStore.getClientById`
    // call site working unchanged while removing that duplicate fetch.
    clients(): Client[] {
      return useClientStore().clients
    },

    getClientById(): (clientId: string) => Client | undefined {
      return (clientId: string) => useClientStore().getClientById(clientId)
    },

    // Same reasoning as clientStore.clientById -- built once per change
    // to `projects`, not per lookup, so getProjectById is O(1) instead of
    // an O(n) `.find()` run once per row by every list that resolves a
    // project name (Tasks, Documents, Payments, Government Submissions,
    // Message Centre, ...).
    projectById(state): Map<string, Project> {
      return new Map(state.projects.map((project) => [project.id, project]))
    },

    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => this.projectById.get(projectId)
    },
  },

  actions: {
    async loadProjects() {
      this.isLoading = true
      this.error = undefined
      try {
        const [projects] = await Promise.all([projectService.getProjects(), useClientStore().loadClients()])
        this.projects = projects
      } catch {
        this.error = 'Unable to load projects. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    // Fetches just the current page/filter/sort combination from the
    // server for the Projects browse table -- the actual pagination fix,
    // as opposed to loadProjects() above which still loads everything
    // (safely, in bounded pages) for cross-reference lookups.
    async loadProjectsPage() {
      this.isPageLoading = true
      this.error = undefined
      try {
        const clientStore = useClientStore()
        if (clientStore.clients.length === 0) {
          await clientStore.loadClients()
        }
        const authStore = useAuthStore()
        const result = await projectService.getProjectsPage({
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          search: this.searchTerm.trim() || undefined,
          status: this.statusFilter !== 'All' ? this.statusFilter : undefined,
          stage: this.stageFilter !== 'All' ? this.stageFilter : undefined,
          priority: this.priorityFilter !== 'All' ? this.priorityFilter : undefined,
          engineerId: this.myProjectsOnly ? authStore.user?.id : undefined,
          deleted: this.showDeleted,
        })
        this.pageItems = result.items
        this.pagination = {
          page: result.page,
          pageSize: result.pageSize,
          total: result.total,
          totalPages: result.totalPages,
        }
      } catch {
        this.error = 'Unable to load projects. Please try again.'
      } finally {
        this.isPageLoading = false
      }
    },

    setPage(page: number) {
      this.pagination.page = page
      void this.loadProjectsPage()
    },

    setPageSize(size: number) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    // Called from the search box's debounced @search event, once the
    // person has paused typing, so we're not firing a request per keystroke.
    applySearch(term: string) {
      this.searchTerm = term
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setStatusFilter(status: ProjectStatus | 'All') {
      this.statusFilter = status
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setStageFilter(stage: WorkflowStage | 'All') {
      this.stageFilter = stage
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setPriorityFilter(priority: ProjectPriority | 'All') {
      this.priorityFilter = priority
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setMyProjectsOnly(value: boolean) {
      this.myProjectsOnly = value
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    setViewMode(mode: ProjectViewMode) {
      this.viewMode = mode
    },

    // Toggles between browsing active projects and browsing soft-deleted
    // ones (the Deleted Projects view, paired with restoreProject below).
    setShowDeleted(value: boolean) {
      this.showDeleted = value
      this.pagination.page = 1
      void this.loadProjectsPage()
    },

    // Persists a project via the backend API.
    async createProject(projectData: ProjectCreateInput): Promise<Project> {
      const project = await projectService.createProject(projectData)
      this.projects = [project, ...this.projects]
      return project
    },

    // Shared by updateProject/setStage/addServices/setStatus/refreshProject below --
    // all patch the same project into both caches after a mutating call succeeds.
    patchProjectInCache(projectId: string, updated: Project): void {
      this.projects = this.projects.map((p) => (p.id === projectId ? updated : p))
      this.pageItems = this.pageItems.map((p) => (p.id === projectId ? updated : p))
    },

    async updateProject(projectId: string, input: ProjectUpdateInput): Promise<Project> {
      const updated = await projectService.updateProject(projectId, input)
      this.patchProjectInCache(projectId, updated)
      return updated
    },

    async setStage(projectId: string, currentStage: string, reason?: string): Promise<Project> {
      const updated = await projectService.setStage(projectId, currentStage, reason)
      this.patchProjectInCache(projectId, updated)
      return updated
    },

    async addServices(projectId: string, input: AddServicesInput): Promise<Project> {
      const updated = await projectService.addServices(projectId, input)
      this.patchProjectInCache(projectId, updated)
      return updated
    },

    async setStatus(projectId: string, status: string, reason?: string): Promise<Project> {
      const updated = await projectService.setStatus(projectId, status, reason)
      this.patchProjectInCache(projectId, updated)
      return updated
    },

    // Re-fetches one project and patches the local cache -- same shape
    // as setStage/setStatus above, for callers (the Payment Plan tab)
    // that mutate a project's data through an endpoint that doesn't
    // itself return the project.
    async refreshProject(projectId: string): Promise<void> {
      const updated = await projectService.getProjectById(projectId)
      if (!updated) return
      this.patchProjectInCache(projectId, updated)
    },

    async deleteProject(projectId: string): Promise<void> {
      await projectService.deleteProject(projectId)
      this.projects = this.projects.filter((p) => p.id !== projectId)
      this.pageItems = this.pageItems.filter((p) => p.id !== projectId)
    },

    // Undoes deleteProject -- restores a soft-deleted project and removes
    // it from the Deleted Projects view's page cache (it belongs back
    // among active projects now, not this list).
    async restoreProject(projectId: string): Promise<Project> {
      const restored = await projectService.restoreProject(projectId)
      this.pageItems = this.pageItems.filter((p) => p.id !== projectId)
      return restored
    },

    clearFilters() {
      this.searchTerm = ''
      this.statusFilter = 'All'
      this.stageFilter = 'All'
      this.priorityFilter = 'All'
      this.myProjectsOnly = false
      this.pagination.page = 1
      void this.loadProjectsPage()
    },
  },
})
