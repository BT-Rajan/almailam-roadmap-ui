import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import type { Client } from '@/types/Client'
import type { Project, ProjectPriority, ProjectStatus, ProjectViewMode, WorkflowStage } from '@/types/Project'

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
  }),

  getters: {
    filteredProjects(state): Project[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.projects.filter((project) => {
        const matchesSearch =
          term.length === 0 ||
          project.projectName.toLowerCase().includes(term) ||
          project.projectNo.toLowerCase().includes(term) ||
          project.engineer.toLowerCase().includes(term)

        const matchesStatus = state.statusFilter === 'All' || project.status === state.statusFilter
        const matchesStage = state.stageFilter === 'All' || project.currentStage === state.stageFilter
        const matchesPriority = state.priorityFilter === 'All' || project.priority === state.priorityFilter

        return matchesSearch && matchesStatus && matchesStage && matchesPriority
      })
    },

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

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setStatusFilter(status: ProjectStatus | 'All') {
      this.statusFilter = status
    },

    setStageFilter(stage: WorkflowStage | 'All') {
      this.stageFilter = stage
    },

    setPriorityFilter(priority: ProjectPriority | 'All') {
      this.priorityFilter = priority
    },

    setViewMode(mode: ProjectViewMode) {
      this.viewMode = mode
    },

    clearFilters() {
      this.searchTerm = ''
      this.statusFilter = 'All'
      this.stageFilter = 'All'
      this.priorityFilter = 'All'
    },
  },
})
