import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import type { ProjectCreateInput } from '@/services/projectService'
import type { Client } from '@/types/Client'
import type { Project, ProjectPriority, ProjectStatus, ProjectViewMode, WorkflowStage } from '@/types/Project'

interface ProjectPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface ProjectStoreState {
  projects: Project[]
  clients: Client[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  statusFilter: ProjectStatus | 'All'
  stageFilter: WorkflowStage | 'All'
  priorityFilter: ProjectPriority | 'All'
  viewMode: ProjectViewMode
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
    clients: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    statusFilter: 'All',
    stageFilter: 'All',
    priorityFilter: 'All',
    viewMode: 'grid',
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
        state.priorityFilter !== 'All'
      )
    },

    getClientById(state) {
      return (clientId: string): Client | undefined => state.clients.find((client) => client.id === clientId)
    },
  },

  actions: {
    async loadProjects() {
      this.isLoading = true
      this.error = undefined
      try {
        const [projects, clients] = await Promise.all([projectService.getProjects(), clientService.getClients()])
        this.projects = projects
        this.clients = clients
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
        if (this.clients.length === 0) {
          this.clients = await clientService.getClients()
        }
        const result = await projectService.getProjectsPage({
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          search: this.searchTerm.trim() || undefined,
          status: this.statusFilter !== 'All' ? this.statusFilter : undefined,
          stage: this.stageFilter !== 'All' ? this.stageFilter : undefined,
          priority: this.priorityFilter !== 'All' ? this.priorityFilter : undefined,
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

    setViewMode(mode: ProjectViewMode) {
      this.viewMode = mode
    },

    addProject(project: Project) {
      this.projects = [project, ...this.projects]
    },

    // Persists a project via the backend API. Prefer this over addProject()
    // above, which only mutates local state and was previously the only
    // path the New Project wizard used -- meaning projects never survived
    // a page refresh and their "project number" was just a client-side
    // guess based on the current in-memory list length (collision-prone
    // and never checked against the server).
    async createProject(projectData: ProjectCreateInput): Promise<Project> {
      const project = await projectService.createProject(projectData)
      this.projects = [project, ...this.projects]
      return project
    },

    clearFilters() {
      this.searchTerm = ''
      this.statusFilter = 'All'
      this.stageFilter = 'All'
      this.priorityFilter = 'All'
      this.pagination.page = 1
      void this.loadProjectsPage()
    },
  },
})
