import { defineStore } from 'pinia'

import { projectService } from '@/services/projectService'
import { taskService } from '@/services/taskService'
import type { TaskInput } from '@/services/taskService'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import type { Project } from '@/types/Project'
import type { Task, TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'

interface TaskStoreState {
  tasks: Task[]
  projects: Project[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  priorityFilter: TaskPriority | 'All'
  projectFilter: string | 'All'
  assigneeFilter: string | 'All'
  selectedTaskId: string | undefined
}

export const useTaskStore = defineStore('task', {
  state: (): TaskStoreState => ({
    tasks: [],
    projects: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    priorityFilter: 'All',
    projectFilter: 'All',
    assigneeFilter: 'All',
    selectedTaskId: undefined,
  }),

  getters: {
    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },

    // Every task belongs to exactly one project, and every project to
    // exactly one client (Project.clientId is required) -- so a task's
    // client is always resolvable transitively through its project.
    // Centralized here rather than in each view so "Unknown Client"
    // fallback wording only lives in one place.
    getClientNameByProjectId(state) {
      return (projectId: string): string => {
        const project = state.projects.find((item) => item.id === projectId)
        if (!project) return 'Unknown Client'
        const clientStore = useClientStore()
        return clientStore.getClientById(project.clientId)?.companyName ?? 'Unknown Client'
      }
    },

    filteredTasks(state): Task[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.tasks.filter((task) => {
        const matchesSearch = term.length === 0 || task.title.toLowerCase().includes(term)
        const matchesPriority = state.priorityFilter === 'All' || task.priority === state.priorityFilter
        const matchesProject = state.projectFilter === 'All' || task.projectId === state.projectFilter
        const matchesAssignee = state.assigneeFilter === 'All' || task.assignedTo === state.assigneeFilter

        return matchesSearch && matchesPriority && matchesProject && matchesAssignee
      })
    },

    hasActiveFilters(state): boolean {
      return (
        state.searchTerm.trim().length > 0 ||
        state.priorityFilter !== 'All' ||
        state.projectFilter !== 'All' ||
        state.assigneeFilter !== 'All'
      )
    },

    tasksByStatus(): Record<TaskStatus, Task[]> {
      const board = { Pending: [], 'In Progress': [], Completed: [] } as Record<TaskStatus, Task[]>
      for (const task of this.filteredTasks) {
        board[task.status].push(task)
      }
      return board
    },

    myTasks(state): Task[] {
      const authStore = useAuthStore()
      const myName = authStore.user?.name
      if (!myName) return []
      return [...state.tasks]
        .filter((task) => task.assignedTo === myName)
        .sort((a, b) => a.dueDate.localeCompare(b.dueDate))
    },

    selectedTask(state): Task | undefined {
      return state.tasks.find((task) => task.id === state.selectedTaskId)
    },

    tasksByProject(state) {
      return (projectId: string): Task[] => state.tasks.filter((task) => task.projectId === projectId)
    },
  },

  actions: {
    async loadTasks() {
      this.isLoading = true
      this.error = undefined
      try {
        const clientStore = useClientStore()
        const [tasks, projects] = await Promise.all([
          taskService.getTasks(),
          projectService.getProjects(),
          clientStore.clients.length === 0 ? clientStore.loadClients() : Promise.resolve(),
        ])
        this.tasks = tasks
        this.projects = projects
      } catch {
        this.error = 'Unable to load tasks. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectTask(taskId: string) {
      this.selectedTaskId = taskId
    },

    clearSelectedTask() {
      this.selectedTaskId = undefined
    },

    // Previously all four of these (status/priority/severity/assignee)
    // only mutated the in-memory task, never called the backend at all
    // -- every change made through the Task Details drawer was
    // completely lost the moment the page was reloaded, even though
    // taskService.updateTask() already existed, fully built and
    // correct, and nothing ever called it.
    async updateTaskStatus(taskId: string, status: TaskStatus, reason?: string) {
      const updated = await taskService.updateTask(taskId, { status, reason })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskPriority(taskId: string, priority: TaskPriority) {
      const updated = await taskService.updateTask(taskId, { priority })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskSeverity(taskId: string, severity: TaskSeverity) {
      const updated = await taskService.updateTask(taskId, { severity })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    // Takes a real user id (e.g. "USR-004"), not a display name --
    // matches what taskService.createTask() already correctly requires
    // (the backend resolves assignedTo to a user id server-side; it was
    // only ever the frontend's TaskFormDialog/TaskAssignmentCard that
    // were sending a name from a hardcoded fake team list instead).
    async updateTaskAssignee(taskId: string, assignedToUserId: string) {
      const updated = await taskService.updateTask(taskId, { assignedTo: assignedToUserId })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async createTask(input: TaskInput): Promise<Task> {
      const task = await taskService.createTask(input)
      this.tasks = [task, ...this.tasks]
      return task
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setPriorityFilter(priority: TaskPriority | 'All') {
      this.priorityFilter = priority
    },

    setProjectFilter(projectId: string | 'All') {
      this.projectFilter = projectId
    },

    setAssigneeFilter(assignee: string | 'All') {
      this.assigneeFilter = assignee
    },

    clearFilters() {
      this.searchTerm = ''
      this.priorityFilter = 'All'
      this.projectFilter = 'All'
      this.assigneeFilter = 'All'
    },
  },
})
