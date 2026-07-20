import { defineStore } from 'pinia'

import { CURRENT_USER_NAME } from '@/constants/team'
import { projectService } from '@/services/projectService'
import { taskService } from '@/services/taskService'
import type { Project } from '@/types/Project'
import type { Task, TaskPriority, TaskStatus } from '@/types/Task'

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
      return [...state.tasks]
        .filter((task) => task.assignedTo === CURRENT_USER_NAME)
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
        const [tasks, projects] = await Promise.all([taskService.getTasks(), projectService.getProjects()])
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

    updateTaskStatus(taskId: string, status: TaskStatus) {
      const task = this.tasks.find((item) => item.id === taskId)
      if (task) task.status = status
    },

    updateTaskPriority(taskId: string, priority: TaskPriority) {
      const task = this.tasks.find((item) => item.id === taskId)
      if (task) task.priority = priority
    },

    updateTaskAssignee(taskId: string, assignedTo: string) {
      const task = this.tasks.find((item) => item.id === taskId)
      if (task) task.assignedTo = assignedTo
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
