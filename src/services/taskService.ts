import { apiClient } from '@/services/httpClient'
import type { PagedResponse, PageParams } from '@/types/Pagination'
import type { Task } from '@/types/Task'
import { fetchAllPages } from '@/utils/fetchAllPages'

export type TaskInput = Omit<Task, 'id'>

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * Fetch a single page of tasks from the backend API. Prefer this over
 * getTasks() for any UI that displays/paginates the list directly, since
 * it only asks the server for one page at a time instead of the whole
 * table.
 */
async function getTasksPage(
  params: PageParams & { projectId?: string; status?: string; assignedTo?: string; priority?: string } = {},
): Promise<PagedResponse<Task>> {
  try {
    const query = buildQuery({
      projectId: params.projectId,
      status: params.status,
      assignedTo: params.assignedTo,
      priority: params.priority,
      search: params.search,
      sort: params.sort,
      page: params.page,
      pageSize: params.pageSize,
    })
    return await apiClient.get<PagedResponse<Task>>(`/api/tasks${query}`)
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch tasks')
  }
}

/**
 * Fetch every task from the backend API as a flat array. Internally walks
 * the paginated endpoint page by page (each request is still bounded
 * server-side) so existing callers that need the full list don't have to
 * change.
 */
async function getTasks(): Promise<Task[]> {
  return fetchAllPages<Task>((page, pageSize) => getTasksPage({ page, pageSize }))
}

/**
 * Fetch a specific task by ID from backend API
 */
async function getTaskById(taskId: string): Promise<Task | undefined> {
  try {
    return await apiClient.get<Task>(`/api/tasks/${taskId}`)
  } catch (error) {
    console.error(`Failed to fetch task ${taskId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch task')
  }
}

/**
 * Create a new task via backend API
 */
async function createTask(input: TaskInput): Promise<Task> {
  try {
    return await apiClient.post<Task>('/api/tasks', input)
  } catch (error) {
    console.error('Failed to create task:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create task')
  }
}

export type TaskUpdateInput = Partial<TaskInput> & { reason?: string }

/**
 * Update a task via backend API
 */
async function updateTask(taskId: string, input: TaskUpdateInput): Promise<Task> {
  try {
    return await apiClient.patch<Task>(`/api/tasks/${taskId}`, input)
  } catch (error) {
    console.error(`Failed to update task ${taskId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update task')
  }
}

/**
 * Delete a task via backend API
 */
async function deleteTask(taskId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/tasks/${taskId}`)
  } catch (error) {
    console.error(`Failed to delete task ${taskId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete task')
  }
}

export const taskService = {
  getTasks,
  getTasksPage,
  getTaskById,
  createTask,
  updateTask,
  deleteTask,
}
