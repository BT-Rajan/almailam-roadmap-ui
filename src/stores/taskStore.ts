import { defineStore } from 'pinia'

import { taskService } from '@/services/taskService'
import type { TaskInput } from '@/services/taskService'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { Project } from '@/types/Project'
import type { Task, TaskStatus } from '@/types/Task'

interface TaskStoreState {
  tasks: Task[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  projectFilter: string | 'All'
  assigneeFilter: string | 'All'
  selectedTaskId: string | undefined
}

export const useTaskStore = defineStore('task', {
  state: (): TaskStoreState => ({
    tasks: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    projectFilter: 'All',
    assigneeFilter: 'All',
    selectedTaskId: undefined,
  }),

  getters: {
    // projectStore is the single, canonical place the full project list
    // lives -- this store used to keep an entirely separate copy fetched
    // independently in loadTasks() below. Delegating means every
    // existing `taskStore.projects` / `taskStore.getProjectById` call
    // site keeps working unchanged, but the actual fetch (and the O(1)
    // id lookup) now happens once, shared with every other store that
    // needs the same data.
    projects(): Project[] {
      return useProjectStore().projects
    },

    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => useProjectStore().getProjectById(projectId)
    },

    // Every task belongs to exactly one project, and every project to
    // exactly one client (Project.clientId is required) -- so a task's
    // client is always resolvable transitively through its project.
    // Centralized here rather than in each view so "Unknown Client"
    // fallback wording only lives in one place.
    getClientNameByProjectId(): (projectId: string) => string {
      return (projectId: string) => {
        const project = useProjectStore().getProjectById(projectId)
        if (!project) return 'Unknown Client'
        return useClientStore().getClientById(project.clientId)?.companyName ?? 'Unknown Client'
      }
    },

    filteredTasks(state): Task[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.tasks.filter((task) => {
        const matchesSearch = term.length === 0 || task.title.toLowerCase().includes(term)
        const matchesProject = state.projectFilter === 'All' || task.projectId === state.projectFilter
        const matchesAssignee = state.assigneeFilter === 'All' || task.assignedTo === state.assigneeFilter

        return matchesSearch && matchesProject && matchesAssignee
      })
    },

    hasActiveFilters(state): boolean {
      return (
        state.searchTerm.trim().length > 0 ||
        state.projectFilter !== 'All' ||
        state.assigneeFilter !== 'All'
      )
    },

    tasksByStatus(): Record<TaskStatus, Task[]> {
      const board = { Preset: [], Pending: [], 'In Progress': [], Completed: [] } as Record<TaskStatus, Task[]>
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
        const projectStore = useProjectStore()
        const clientStore = useClientStore()
        await Promise.all([
          taskService.getTasks().then((tasks) => {
            this.tasks = tasks
          }),
          projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
          clientStore.clients.length === 0 ? clientStore.loadClients() : Promise.resolve(),
        ])
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
    // correct, and nothing ever called it. (Priority/Severity are no
    // longer editable from the UI at all -- see updateTaskPriority/
    // updateTaskSeverity removal -- but the fields themselves still
    // exist on Task, defaulted server-side.)
    async updateTaskTitle(taskId: string, title: string) {
      const updated = await taskService.updateTask(taskId, { title })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskStatus(taskId: string, status: TaskStatus, reason?: string) {
      const updated = await taskService.updateTask(taskId, { status, reason })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskStartDate(taskId: string, startDate: string) {
      const updated = await taskService.updateTask(taskId, { startDate })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskDueDate(taskId: string, dueDate: string) {
      const updated = await taskService.updateTask(taskId, { dueDate })
      this.tasks = this.tasks.map((task) => (task.id === taskId ? updated : task))
    },

    async updateTaskDueTime(taskId: string, dueTime: string) {
      const updated = await taskService.updateTask(taskId, { dueTime })
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

    async deleteTask(taskId: string): Promise<void> {
      await taskService.deleteTask(taskId)
      this.tasks = this.tasks.filter((task) => task.id !== taskId)
      if (this.selectedTaskId === taskId) this.selectedTaskId = undefined
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setProjectFilter(projectId: string | 'All') {
      this.projectFilter = projectId
    },

    setAssigneeFilter(assignee: string | 'All') {
      this.assigneeFilter = assignee
    },

    clearFilters() {
      this.searchTerm = ''
      this.projectFilter = 'All'
      this.assigneeFilter = 'All'
    },
  },
})
