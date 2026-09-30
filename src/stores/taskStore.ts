import { defineStore } from 'pinia'

import { taskService } from '@/services/taskService'
import type { TaskInput } from '@/services/taskService'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { Project } from '@/types/Project'
import type { Task, TaskAuditEvent, TaskStatus } from '@/types/Task'
import { CACHE_TTL_MS, getLoadGate } from '@/utils/loadGate'
import { replaceScope } from '@/utils/scopedCollection'
import { describeStoreError } from '@/utils/storeError'

interface TaskStoreState {
  tasks: Task[]
  // True only once loadTasks() has fetched EVERY task. `tasks` can also hold
  // just some projects' rows (see loadTasksForProject), so `tasks.length`
  // says nothing about completeness -- anything that needs the whole list
  // must check this flag (via needsFullLoad), not the array length.
  isFullyLoaded: boolean
  isFullLoading: boolean
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  // Task Board filters -- applied by the server (project number / user
  // id), not to a downloaded list.
  projectFilter: string | 'All'
  assigneeFilter: string | 'All'
  // Task Board: each status column is its own server page (newest data,
  // bounded), not a slice of every task ever created. Kept apart from
  // `tasks` (the per-project/per-user cache) so a filtered board can
  // never pass for a project's full task list.
  board: Record<TaskStatus, Task[]>
  boardTotals: Record<TaskStatus, number>
  boardPages: Record<TaskStatus, number>
  isBoardLoading: boolean
  // One task's own history (status changes, reassignment, schedule
  // edits, notes -- see TaskHistoryPanel.vue), keyed by task id. Same
  // shape/loading pattern as statusReportStore.taskReports.
  auditEventsByTask: Record<string, TaskAuditEvent[]>
  isHistoryLoading: boolean
  historyError: string | undefined
}

const BOARD_STATUSES: TaskStatus[] = ['Preset', 'Pending', 'In Progress', 'Completed']
const BOARD_PAGE_SIZE = 30

function emptyBoard(): Record<TaskStatus, Task[]> {
  return { Preset: [], Pending: [], 'In Progress': [], Completed: [] }
}

export const useTaskStore = defineStore('task', {
  state: (): TaskStoreState => ({
    tasks: [],
    isFullyLoaded: false,
    isFullLoading: false,
    isLoading: false,
    error: undefined,
    searchTerm: '',
    projectFilter: 'All',
    assigneeFilter: 'All',
    board: emptyBoard(),
    boardTotals: { Preset: 0, Pending: 0, 'In Progress': 0, Completed: 0 },
    boardPages: { Preset: 0, Pending: 0, 'In Progress': 0, Completed: 0 },
    isBoardLoading: false,
    auditEventsByTask: {},
    isHistoryLoading: false,
    historyError: undefined,
  }),

  getters: {
    // Whether a caller that needs every task should start a full load: not
    // already loaded, and not already being loaded.
    needsFullLoad(state): boolean {
      return !state.isFullyLoaded && !state.isFullLoading
    },

    // projectStore is the single, canonical place the full project list
    // lives -- delegating shares one fetch and O(1) lookup with every
    // other store that needs the same data.
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

    hasActiveFilters(state): boolean {
      return state.projectFilter !== 'All' || state.assigneeFilter !== 'All'
    },

    tasksByStatus(state): Record<TaskStatus, Task[]> {
      return state.board
    },

    myTasks(state): Task[] {
      const authStore = useAuthStore()
      const myName = authStore.user?.name
      if (!myName) return []
      return [...state.tasks]
        .filter((task) => task.assignedTo === myName)
        .sort((a, b) => a.dueDate.localeCompare(b.dueDate))
    },

    tasksByProject(state) {
      return (projectId: string): Task[] => state.tasks.filter((task) => task.projectId === projectId)
    },
  },

  actions: {
    async loadTasks() {
      this.isLoading = true
      this.isFullLoading = true
      this.error = undefined
      try {
        const projectStore = useProjectStore()
        const clientStore = useClientStore()
        await Promise.all([
          taskService.getTasks().then((tasks) => {
            this.tasks = tasks
            this.isFullyLoaded = true
          }),
          !projectStore.isFullyLoaded ? projectStore.loadProjects() : Promise.resolve(),
          !clientStore.isFullyLoaded ? clientStore.loadClients() : Promise.resolve(),
        ])
      } catch (error) {
        this.error = describeStoreError('Unable to load tasks. Please try again.', error)
      } finally {
        this.isLoading = false
        this.isFullLoading = false
      }
    },

    // Just the signed-in user's own tasks (server-side assignee filter) --
    // what My Tasks shows. Each task carries its project/client names, so
    // no project or client list is needed either. Merged into `tasks` in
    // place of this user's old rows; does NOT mark the list fully loaded.
    async loadMyTasks() {
      const authStore = useAuthStore()
      const me = authStore.user
      if (!me) return
      this.isLoading = true
      this.error = undefined
      try {
        const mine = await taskService.getTasksAssignedTo(me.id)
        this.tasks = replaceScope(this.tasks, mine, (task) => task.assignedTo === me.name)
      } catch (error) {
        this.error = describeStoreError('Unable to load tasks. Please try again.', error)
      } finally {
        this.isLoading = false
      }
    },

    // Loads just one project's tasks, merging them into `tasks` in place of
    // that project's old rows -- for views scoped to a single project (its
    // workspace), which shouldn't download every task in the company just to
    // show its own. Does NOT mark the list fully loaded. A no-op when every
    // task is already here, unless `force` (use it after something changes
    // this project's tasks server-side, e.g. a stage change auto-creating
    // service tasks).
    async loadTasksForProject(projectId: string, options: { force?: boolean } = {}) {
      if (this.isFullyLoaded && !options.force) return
      await getLoadGate(this, `project:${projectId}`, CACHE_TTL_MS).run(async (isCurrent) => {
        this.isLoading = true
        this.error = undefined
        try {
          const projectTasks = await taskService.getTasksForProject(projectId)
          if (isCurrent()) {
            this.tasks = replaceScope(this.tasks, projectTasks, (task) => task.projectId === projectId)
          }
          return true
        } catch (error) {
          if (isCurrent()) this.error = describeStoreError('Unable to load tasks. Please try again.', error)
          return false
        } finally {
          if (isCurrent()) this.isLoading = false
        }
      }, options)
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
    // One task by id, fetching just it when not cached -- for the task
    // page opened from a link, instead of downloading every task.
    async ensureTask(taskId: string): Promise<Task | undefined> {
      const cached = this.tasks.find((task) => task.id === taskId)
      if (cached) return cached
      const task = await taskService.getTaskById(taskId)
      if (task && !this.tasks.some((item) => item.id === taskId)) this.tasks = [...this.tasks, task]
      return task
    },

    async updateTaskTitle(taskId: string, title: string) {
      const updated = await taskService.updateTask(taskId, { title })
      this._patchTask(updated)
    },

    async updateTaskStatus(taskId: string, status: TaskStatus, reason?: string) {
      const updated = await taskService.updateTask(taskId, { status, reason })
      this._patchTask(updated)
    },

    async updateTaskStartDate(taskId: string, startDate: string) {
      const updated = await taskService.updateTask(taskId, { startDate })
      this._patchTask(updated)
    },

    async updateTaskDueDate(taskId: string, dueDate: string) {
      const updated = await taskService.updateTask(taskId, { dueDate })
      this._patchTask(updated)
    },

    async updateTaskDueTime(taskId: string, dueTime: string) {
      const updated = await taskService.updateTask(taskId, { dueTime })
      this._patchTask(updated)
    },

    // Takes a real user id (e.g. "USR-004"), not a display name --
    // matches what taskService.createTask() already correctly requires
    // (the backend resolves assignedTo to a user id server-side; it was
    // only ever the frontend's TaskFormDialog/TaskAssignmentCard that
    // were sending a name from a hardcoded fake team list instead).
    async updateTaskAssignee(taskId: string, assignedToUserId: string) {
      const updated = await taskService.updateTask(taskId, { assignedTo: assignedToUserId })
      this._patchTask(updated)
    },

    // Puts an updated task back everywhere it's shown: the per-project/user
    // cache and, if it's on the Task Board, its (possibly new) column.
    _patchTask(updated: Task) {
      this.tasks = this.tasks.map((task) => (task.id === updated.id ? updated : task))
      const from = BOARD_STATUSES.find((status) => this.board[status].some((task) => task.id === updated.id))
      if (!from) return
      if (from === updated.status) {
        this.board[from] = this.board[from].map((task) => (task.id === updated.id ? updated : task))
        return
      }
      this.board[from] = this.board[from].filter((task) => task.id !== updated.id)
      this.board[updated.status] = [updated, ...this.board[updated.status]]
      this.boardTotals[from] = Math.max(0, this.boardTotals[from] - 1)
      this.boardTotals[updated.status] += 1
    },

    // Task Board: the first page of every status column, filtered by the
    // server. Completed shows the most recently due first; open columns
    // the soonest due.
    async loadBoard() {
      this.isBoardLoading = true
      this.error = undefined
      try {
        const pages = await Promise.all(BOARD_STATUSES.map((status) => this._fetchBoardPage(status, 1)))
        const board = emptyBoard()
        BOARD_STATUSES.forEach((status, index) => {
          board[status] = pages[index].items
          this.boardTotals[status] = pages[index].total
          this.boardPages[status] = 1
        })
        this.board = board
      } catch (error) {
        this.error = describeStoreError('Unable to load tasks. Please try again.', error)
      } finally {
        this.isBoardLoading = false
      }
    },

    // The next page of one Task Board column.
    async loadMoreBoard(status: TaskStatus) {
      try {
        const next = await this._fetchBoardPage(status, this.boardPages[status] + 1)
        const seen = new Set(this.board[status].map((task) => task.id))
        this.board[status] = [...this.board[status], ...next.items.filter((task) => !seen.has(task.id))]
        this.boardTotals[status] = next.total
        this.boardPages[status] += 1
      } catch (error) {
        this.error = describeStoreError('Unable to load tasks. Please try again.', error)
      }
    },

    _fetchBoardPage(status: TaskStatus, page: number) {
      return taskService.getTasksPage({
        status,
        projectId: this.projectFilter !== 'All' ? this.projectFilter : undefined,
        assignedTo: this.assigneeFilter !== 'All' ? this.assigneeFilter : undefined,
        sort: status === 'Completed' ? '-dueDate' : 'dueDate',
        page,
        pageSize: BOARD_PAGE_SIZE,
      })
    },

    async createTask(input: TaskInput): Promise<Task> {
      const task = await taskService.createTask(input)
      this.tasks = [task, ...this.tasks]
      return task
    },

    async deleteTask(taskId: string): Promise<void> {
      await taskService.deleteTask(taskId)
      this.tasks = this.tasks.filter((task) => task.id !== taskId)
      for (const status of BOARD_STATUSES) {
        if (this.board[status].some((task) => task.id === taskId)) {
          this.board[status] = this.board[status].filter((task) => task.id !== taskId)
          this.boardTotals[status] = Math.max(0, this.boardTotals[status] - 1)
        }
      }
    },

    async loadAuditEvents(taskId: string) {
      this.isHistoryLoading = true
      this.historyError = undefined
      try {
        this.auditEventsByTask = { ...this.auditEventsByTask, [taskId]: await taskService.getAuditEvents(taskId) }
      } catch (error) {
        this.historyError = describeStoreError("Unable to load this task's history. Please try again.", error)
      } finally {
        this.isHistoryLoading = false
      }
    },

    async addNote(taskId: string, note: string) {
      this.auditEventsByTask = { ...this.auditEventsByTask, [taskId]: await taskService.addNote(taskId, note) }
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setProjectFilter(projectId: string | 'All') {
      this.projectFilter = projectId
      void this.loadBoard()
    },

    // A user id (the server filters on it), not a display name.
    setAssigneeFilter(assigneeUserId: string | 'All') {
      this.assigneeFilter = assigneeUserId
      void this.loadBoard()
    },

    clearFilters() {
      this.searchTerm = ''
      this.projectFilter = 'All'
      this.assigneeFilter = 'All'
      void this.loadBoard()
    },
  },
})
