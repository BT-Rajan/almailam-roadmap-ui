import { apiClient } from '@/services/httpClient'
import type { Task } from '@/types/Task'

export type TaskInput = Omit<Task, 'id'>

/**
 * Fetch all tasks from backend API
 */
async function getTasks(): Promise<Task[]> {
  try {
    return await apiClient.get<Task[]>('/api/tasks')
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch tasks')
  }
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

/**
 * Update a task via backend API
 */
async function updateTask(taskId: string, input: Partial<TaskInput>): Promise<Task> {
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
  getTaskById,
  createTask,
  updateTask,
  deleteTask,
}
